# S2-Gate 583 Status: Resident Frame Accounting DQ Ledger

## Gate

- Gate: S2-Gate 583
- Title: Resident frame-accounting DQ ledger
- Status: green
- Date: 2026-06-23

## Completed Content

- Extended `frame_accounting.json` so each resident calibrated-light row can
  carry the Gate582 embedded DQ/mask contract evidence:
  - resident source-DQ contract availability, status, pass flag, and execution
    route;
  - resident calibrated-light DQ/mask contract availability, status, pass flag,
    contract sources, and frame-mask sources;
  - resident calibrated-light frame-mask contract availability and pass flag.
- Added resident DQ/mask contract fields to exception-frame accounting so
  quality-rejected or zero-weight frames remain auditable.
- Added summary counters for resident calibrated-light DQ contract rows,
  passing/failing contracts, source-DQ contract rows, frame-mask contract rows,
  and distinct contract sources.
- Updated the HTML report frame-accounting summary and per-frame table to expose
  the resident DQ/mask ledger.
- Updated Phase 2 documentation and algorithm-source independence log.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_frame_accounting.py`
- `.venv\Scripts\python.exe -m ruff check src\glass\engine\frame_accounting.py src\glass\report\html_report.py tests\test_frame_accounting.py`
- `.venv\Scripts\python.exe -m py_compile src\glass\engine\frame_accounting.py src\glass\report\html_report.py tests\test_frame_accounting.py`
- `.venv\Scripts\glass.exe pipeline-contract --run C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3 --out C:\glass_runs\phase2_s2_gate583_frame_accounting_ledger\pipeline_contract_after_frame_accounting.json --markdown C:\glass_runs\phase2_s2_gate583_frame_accounting_ledger\pipeline_contract_after_frame_accounting.md --pixel-verify`
- `.venv\Scripts\glass.exe report --run C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3 --out C:\glass_runs\phase2_s2_gate583_frame_accounting_ledger\report.html --pipeline-contract C:\glass_runs\phase2_s2_gate583_frame_accounting_ledger\pipeline_contract_after_frame_accounting.json`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused frame-accounting tests: `4 passed in 0.19s`
- Ruff: `All checks passed!`
- Py compile: passed
- Full pytest: `1249 passed in 52.14s`

## Real 200-Light Validation

- Source run:
  `C:\glass_runs\phase2_s2_gate582_resident_calibration_ledger\default_v3`
- Gate583 evidence directory:
  `C:\glass_runs\phase2_s2_gate583_frame_accounting_ledger`
- Frame-accounting validation:
  `C:\glass_runs\phase2_s2_gate583_frame_accounting_ledger\frame_accounting_ledger_validation.json`
- Pixel-verified pipeline contract:
  `C:\glass_runs\phase2_s2_gate583_frame_accounting_ledger\pipeline_contract_after_frame_accounting.json`
- HTML report:
  `C:\glass_runs\phase2_s2_gate583_frame_accounting_ledger\report.html`
- Frame-accounting rows: `200`
- Resident calibrated-light DQ contract rows: `200`
- Passing resident calibrated-light DQ contracts: `200`
- Failed resident calibrated-light DQ contracts: `0`
- Resident source-DQ contract rows: `200`
- Resident frame-mask contract rows: `200`
- Resident DQ/mask contract source: `resident_source_dq_execution`
- Resident frame-mask source: `resident_frame_masks`
- Final frame statuses: `193` integrated, `7` quality rejected
- Pixel-verified pipeline-contract status: `passed`
- Existing Gate582 SHA256 parity artifact remains green for all six integration
  FITS outputs against the Gate579 current default output.

## CUDA Status

- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Driver version: 596.21
- VRAM: 97886 MiB

## Known Limitations

- This gate strengthens the canonical frame-accounting/report audit surface.
- It does not add a new DQ detector, change source-DQ policy, change frame
  admission, change registration/warp/LN/rejection/integration math, or optimize
  runtime.
- The report can now display the resident DQ/mask contract, but the authoritative
  machine-readable surface is `frame_accounting.json`.

## Next Step

- Return to the substantive Phase 2 mainline: StackEngine default path,
  DQ/mask pipeline contract completion, real 200-light regression, and resident
  CUDA performance/numerical consistency work. Avoid further release-only or
  report-only gates unless they directly unblock those objectives.

## Clean-Room Compliance

- Compliant. This gate uses only GLASS-generated resident calibration,
  source-DQ, frame-mask, frame-accounting, pipeline-contract, integration, and
  report artifacts.
- No official external stacking implementation source was read, summarized,
  copied, or reworked.
- Input image directories were treated as read-only.
