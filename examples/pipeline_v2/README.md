# Battery measurement examples

Import one CSV at a time in the Prediction Engine.

`single.csv` and `history.csv` contain measured records for held-out battery 2
from `master_dataset.csv`, with targets/discharge capacity removed. The single
example contains its first recorded cycle; the history example contains its
first 20 recorded cycles. No values or labels were synthesized.

- `single.csv`: one observed cycle for an SOH assessment.
- `history.csv`: observed history for an SOH and RUL assessment.
- `battery_72_history_to_cycle_492.csv`: all 492 recorded observations for
  battery 72 through cycle 492, extracted unchanged from
  `ml/data/master_dataset.csv`. Includes only the eight accepted measurement
  fields; excludes targets and observations after cycle 492.

`presentation_inputs/battery_72_near_80_soh.csv` now contains cycles 491 and
492 after regenerating it with `get_demo_data.py`. A single cycle on its own
has no preceding history, so its RUL response is legitimately null. The full
history example supplies all preceding measurements. Against
the v2.0.1 bundle, the API returns approximately 18.4 remaining cycles for
that history (18 cycles at the dashboard's whole-cycle precision).

SOH can differ between single-record and history assessments because the
submitted observations differ. Neither example substitutes measured target
values for API predictions.

Run frontend checks from `frontend/`:

```text
npm test
npm run build
node tests/browser.mjs
node tests/browser.mjs --live-api
```

The optional browser checks use an installed Chrome (`BROWSER_PATH` can
override its location). `--live-api` also verifies both battery 72 CSVs
against the running backend configured by the frontend.
