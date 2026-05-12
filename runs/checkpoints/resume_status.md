# Resume Status

- Date: 2026-05-12
- Status: improved

## Completed

- `gpwbpp run` now writes `processing_plan.json` into the run directory.
- When the plan's manifest path exists, `gpwbpp run` also writes `manifest.json` into the run directory.
- `gpwbpp resume` can continue a run directory from existing artifacts instead of requiring the original command context.
- Resume skips existing calibration artifacts and continues from later stage artifacts when present.

## Commands Run

```powershell
.\.venv\Scripts\python -m pytest -q tests/test_pipeline_fixture.py::test_resume_continues_from_warp_without_repeating_calibration tests/test_pipeline_fixture.py
.\.venv\Scripts\python -m pytest -q
```

## Test Result

- Pipeline fixture tests: 9 passed.
- Full suite: 50 passed.

## Known Limitations

- Resume still uses artifact presence, not full checksum validation.
- Resume default backend/tile settings are `auto` and `512` if resuming through the simple CLI.

## Clean-room Compliance

- Resume changes do not touch PixInsight/WBPP/PJSR source or user input data.
