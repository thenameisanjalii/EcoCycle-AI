"""Fetch measured C/3 characterizations by HTTP ranges, never whole ZIPs.

Sampling fixed before discharge labels: cycle 0, every 400 ageing cycles,
and the last available characterization of each of the twenty cells.
Keep compressed original entries locally; ZIP CRC and SHA256 are recorded.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import io
import json
from pathlib import Path
import re
import time
import zipfile
import zlib

import numpy as np
import pandas as pd
import requests

from .fetch_soh_measurements import DEST, BASE


class RangeFile(io.RawIOBase):
    def __init__(self, url, size):
        self.url, self.size, self.position = url, size, 0
        self.session = requests.Session()

    def seekable(self):
        return True

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else (self.position if whence == 1 else self.size) + offset
        return self.position

    def tell(self):
        return self.position

    def read(self, size=-1):
        end = self.size if size < 0 else min(self.size, self.position + size)
        if self.position >= end:
            return b""
        start = self.position
        for attempt in range(4):
            try:
                response = self.session.get(self.url, headers={"Range": f"bytes={start}-{end-1}"}, timeout=90)
                response.raise_for_status()
                if response.status_code != 206 or len(response.content) != end - start:
                    raise ValueError("Server must honor exact HTTP ranges; whole-archive fallback forbidden")
                self.position = end
                return response.content
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)


def extract_measurements(content):
    # Keep both discharge (step 11) and charge (step 13); never use C/25
    # or the publisher's charge-based SOH as discharge labels.
    frame = pd.read_csv(io.BytesIO(content), sep=";", usecols=[
        "Step_Index", "Step_Time", "Current", "Voltage", "Charge_Capacity", "Discharge_Capacity"])
    # Publisher CSV blocks can be stored out of time order. Never interpret
    # physical file order as a step's end; order by recorded step time.
    discharge = frame[frame.Step_Index == 11].sort_values("Step_Time")
    charge = frame[frame.Step_Index == 13].sort_values("Step_Time")
    if discharge.empty or charge.empty:
        return {"status": "missing_C3_step"}
    values = dict(QDischarge=float(discharge.Discharge_Capacity.max()),
                  QCharge=float(charge.Charge_Capacity.max()),
                  chargetime=float(charge.Step_Time.max() / 60),
                  discharge_current_median_A=float(discharge.Current.median()),
                  charge_current_median_A=float(charge.Current.median()),
                  discharge_voltage_start_V=float(discharge.Voltage.iloc[0]),
                  discharge_voltage_end_V=float(discharge.Voltage.iloc[-1]),
                  discharge_step_rows=len(discharge), charge_step_rows=len(charge))
    if not np.isfinite(list(values.values())).all():
        return {"status": "nonfinite_measurement", **values}
    # Known aborted characterization at cycle 100 is outside our fixed grid;
    # require a completed discharge down to the protocol limit, not a capacity cutoff.
    values["status"] = "ok" if (values["QDischarge"] > 0 and values["QCharge"] > 0
        and values["discharge_voltage_start_V"] > 3.3 and values["discharge_voltage_end_V"] <= 2.51
        and -.39 < values["discharge_current_median_A"] < -.34) else "incomplete_or_wrong_protocol"
    return values


def fetch_cell(file, stride):
    metadata = file["dataFile"]
    name = file["label"].removesuffix(".zip")
    directory = DEST / "raw_characterizations" / name
    directory.mkdir(parents=True, exist_ok=True)
    report = directory / "measurements.json"
    if report.exists():
        cached = json.loads(report.read_text())
        if cached["stride"] != stride:
            raise ValueError("Cached sampling stride differs")
        for row in cached["records"]:
            if hashlib.sha256((directory / row["cache_file"]).read_bytes()).hexdigest() != row["compressed_sha256"]:
                raise ValueError("Cached raw entry changed")
        return cached["records"]
    url = f"{BASE}/api/access/datafile/{metadata['id']}"
    remote = RangeFile(url, metadata["filesize"])
    records = []
    with zipfile.ZipFile(remote) as archive:
        entries = [(int(re.search(r"charac(\d+)\.csv$", entry.filename)[1]), entry)
            for entry in archive.infolist()
            if "/agingdata_50degC/" in entry.filename and re.search(r"charac\d+\.csv$", entry.filename)]
        last = max(c for c, _ in entries)
        for cycle, entry in sorted(entries):
            if cycle % stride and cycle != last:
                continue
            # Retain source-compressed bytes, not lossy/synthesized summaries.
            remote.seek(entry.header_offset)
            header = remote.read(30)
            name_length = int.from_bytes(header[26:28], "little")
            extra_length = int.from_bytes(header[28:30], "little")
            remote.seek(entry.header_offset + 30 + name_length + extra_length)
            compressed = remote.read(entry.compress_size)
            if entry.compress_type != zipfile.ZIP_DEFLATED:
                raise ValueError("Expected deflate ZIP member")
            content = zlib.decompress(compressed, -15)
            if len(content) != entry.file_size or zlib.crc32(content) != entry.CRC:
                raise ValueError("ZIP member integrity failure")
            cache_file = f"charac{cycle:04d}.deflate"
            cache_path = directory / cache_file
            if cache_path.exists():
                if cache_path.read_bytes() != compressed:
                    raise ValueError("Existing raw file differs")
            else:
                cache_path.write_bytes(compressed)
            row = dict(source_cell_id=name, cycle=cycle, source_url=url, source_entry=entry.filename,
                source_archive_md5=metadata["checksum"]["value"], zip_crc32=f"{entry.CRC:08x}",
                source_sha256=hashlib.sha256(content).hexdigest(), cache_file=cache_file,
                compressed_sha256=hashlib.sha256(compressed).hexdigest(), **extract_measurements(content))
            records.append(row)
            print(name, cycle, row["status"], flush=True)
    report.write_text(json.dumps({"stride": stride, "records": records}, indent=2), encoding="utf-8")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stride", type=int, default=400)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--cells", nargs="*", help="Fetch selected source cells to cache only")
    parser.add_argument("--reaudit-cached", action="store_true", help="Re-extract summaries locally after parser changes, no network")
    args = parser.parse_args()
    if args.reaudit_cached:
        results = []
        for report in sorted((DEST / "raw_characterizations").glob("*/measurements.json")):
            cached = json.loads(report.read_text())
            for row in cached["records"]:
                compressed = (report.parent / row["cache_file"]).read_bytes()
                if hashlib.sha256(compressed).hexdigest() != row["compressed_sha256"]:
                    raise ValueError("Cached raw entry changed")
                content = zlib.decompress(compressed, -15)
                if hashlib.sha256(content).hexdigest() != row["source_sha256"]:
                    raise ValueError("Raw measurement hash differs")
                row.update(extract_measurements(content))
                results.append(row)
            report.write_text(json.dumps(cached, indent=2), encoding="utf-8")
        if len({r["source_cell_id"] for r in results}) != 20:
            raise ValueError("All twenty cells must be acquired before re-audit")
        pd.DataFrame(results).sort_values(["source_cell_id", "cycle"]).to_csv(DEST / "discharge_measurements.csv", index=False)
        print("Re-audited", len(results), "cached measured characterizations without network")
        return
    metadata = json.loads((DEST / "dataset_metadata.json").read_text(encoding="utf-8"))
    files = [f for f in metadata["data"]["latestVersion"]["files"] if f["label"].endswith(".zip")]
    if args.cells:
        files = [f for f in files if f["label"].removesuffix(".zip") in args.cells]
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(fetch_cell, file, args.stride) for file in files]
        for future in as_completed(futures):
            results.extend(future.result())
    if args.cells:
        print("Selected cells cached; complete twenty-cell export remains separate", flush=True)
        return
    path = DEST / "discharge_measurements.csv"
    with path.open("x", newline="", encoding="utf-8") as stream:
        pd.DataFrame(results).sort_values(["source_cell_id", "cycle"]).to_csv(stream, index=False)
    print("Saved", len(results), "actual characterization measurements", flush=True)


if __name__ == "__main__":
    main()
