# Verification record

Reference bundle: `run-20261111-v2.0.1`.
Registry SHA-256: `72b52eda2ff4c0e90226b6d46ad983c0c54567858a8cfdd23ea3f03ec53023be`.

- `python -m pytest -q -p no:cacheprovider`: **111 passed**; existing FastAPI/Starlette deprecation warnings remain.
- `npm.cmd --prefix frontend test`: **3 passed**, covering request cancellation, stale response rejection and upload races.
- `npm.cmd --prefix frontend run build`: **passed**, including TypeScript checks and the Vite production build. Vite emits the existing bundle-size advisory (main JS about 603 kB); no build errors.
- The parity verifier passed for all **18,512 held-out single assessments** and **21 full battery histories**. Offline/API results match exactly; latest history outputs match saved test predictions.
- Both documented offline CLI contracts completed on the measured CSV examples; example output JSONs are saved here.
- **38 original files** (all original CSVs, models/preprocessors and the locked registry) retain their original SHA-256 hashes.
- Integer battery/row metadata types, sensor faults on unseen battery IDs, train-only parameters, past-only features, missing history, censoring, confirmation gaps, physical/leakage rejection, singleton batches, mixed/duplicate histories, registry/file tampering and non-overwriting training are covered.

API verification uses FastAPI TestClient. Frontend regression checks execute the actual request gate; no browser end-to-end UI test or Docker build was performed. No changes were pushed. The pre-existing untracked `frontend/.vite/` directory was left untouched.
