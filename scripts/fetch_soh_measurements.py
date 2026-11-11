"""Download the publisher's small, measured summaries (not 26 GB of raw ZIPs).

python -m scripts.fetch_soh_measurements
Files are pinned to Recherche Data Gouv dataset V2, DOI 10.57745/OLBXKT.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "ml/data/sources/wheeler2025"
BASE = "https://entrepot.recherche.data.gouv.fr"
FILES = {
    "extractedData.mat": (606807, "6a468312420585734784ea763ea6e0c3"),
    "Matlab_BasicImportAndDisplay.m": (607239, "8c26d8e099aadfbb1c7633d235374180"),
    "readme.txt": (611322, "363da70a34c59bc96f87ae735702b3f7"),
    "WLTPcycle.txt": (606698, "adcd406ab3229093a30bedd4ee2311f3"),
}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    metadata_path = DEST / "dataset_metadata.json"
    if not metadata_path.exists():
        response = requests.get(f"{BASE}/api/datasets/:persistentId/versions/2.0",
            params={"persistentId": "doi:10.57745/OLBXKT"}, timeout=90)
        response.raise_for_status()
        version = response.json()["data"]
        if (version["versionNumber"], version["versionMinorNumber"]) != (2, 0):
            raise ValueError("Expected pinned dataset version 2.0")
        metadata_path.write_text(json.dumps({"data": {"latestVersion": version}}, indent=2), encoding="utf-8")
    records = []
    for name, (file_id, checksum) in FILES.items():
        url = f"{BASE}/api/access/datafile/{file_id}"
        path = DEST / name
        if not path.exists():
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            content = response.content
            if hashlib.md5(content).hexdigest() != checksum:
                raise ValueError(f"Publisher checksum mismatch: {name}")
            with path.open("xb") as stream:
                stream.write(content)
        content = path.read_bytes()
        if hashlib.md5(content).hexdigest() != checksum:
            raise ValueError(f"Publisher checksum mismatch: {name}")
        records.append(dict(file=name, url=url, bytes=len(content), md5=checksum,
                            sha256=hashlib.sha256(content).hexdigest()))
        print(name, len(content), flush=True)
    manifest = DEST / "download_manifest.json"
    if not manifest.exists():
        manifest.write_text(json.dumps({"dataset_doi": "10.57745/OLBXKT", "version": "2.0",
            "retrieved_utc": datetime.now(timezone.utc).isoformat(), "files": records}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
