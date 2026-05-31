# S2-Gate 4 Status: DQ/Mask Propagation

Date: 2026-05-31

## Gate

S2-Gate 4: DQ/mask propagation across calibration, warp, local normalization,
and integration.

## Completed Content

- Added `src/glass/engine/dq.py` with shared DQ artifact helpers:
  - `dq_header`
  - `dq_summary`
  - `dq_mask_from_invalid`
  - `dq_mask_from_coverage`
  - `write_dq_tile`
  - `add_summary_counts`
  - `write_full_dq_map`
- Calibration now writes one DQ FITS map per calibrated light under
  `calib_cache/dq/` and records `dq_mask_path` plus `dq_summary` in
  `calibration_artifacts.json`.
- Warp now writes one DQ FITS map per accepted registered frame under
  `dq_cache/` and records `dq_mask_path` plus `dq_summary` in
  `warp_results.json`.
- Local normalization now propagates passthrough DQ when disabled and writes
  local-normalization exclusion DQ maps when enabled.
- Integration now writes one `dq_map_<filter>.fits` per integrated output and
  records `dq_map_path` plus `dq_summary` in `integration_results.json`.
- HTML report now includes a DQ/mask summary table.
- Added tests that verify DQ helper behavior and the presence of DQ artifacts in
  calibration, warp, local normalization, integration, and report outputs.
- Updated `docs/algorithm_sources.md` for the DQ propagation implementation.

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q tests\test_pipeline_fixture.py tests\test_stack_engine.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_phase2_contracts.py tests\test_pipeline_fixture.py tests\test_stack_engine.py`
- `.venv\Scripts\python.exe -m pytest -q`
- Synthetic representative smoke:
  - generated `runs\s2_gate_04_smoke\synthetic`
  - ran `audit` to `runs\s2_gate_04_smoke\run`
  - backend: `cpu`
  - tile size: `12`
  - local normalization: `on`
  - integration rejection: `winsorized_sigma`
- CUDA probe through `.venv\Scripts\python.exe` importing `glass_cuda`.
- `git diff --stat`
- `git status --short`

## Test Result

- Focused DQ/pipeline tests: `32 passed in 5.26s`
- Full test suite: `207 passed in 11.50s`

## Representative Smoke Result

Smoke run summary:

- Synthetic generation return code: `0`
- Audit return code: `0`
- Wall elapsed including generation and audit: approximately `0.573 s`
- `calibration_dq`: `true`
- `warp_dq`: `true`
- `local_norm_dq`: `true`
- `integration_dq`: `true`
- `report_has_dq`: `true`

Smoke artifacts:

- `runs\s2_gate_04_smoke\run\calibration_artifacts.json`
- `runs\s2_gate_04_smoke\run\warp_results.json`
- `runs\s2_gate_04_smoke\run\local_norm_results.json`
- `runs\s2_gate_04_smoke\run\integration_results.json`
- `runs\s2_gate_04_smoke\run\report.html`

## CUDA Availability

CUDA is available to GLASS in the current environment.

- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Driver version: `596.21`
- Total VRAM: `97886 MiB`
- Multiprocessors: `188`
- Native backend loaded: yes

## Known Limitations

- DQ maps are currently written as float32 FITS images containing integer
  bitfield values because the existing tile writer is float32-oriented.
- Calibration currently marks non-finite calibrated pixels as `NO_DATA`; hot,
  cold, dead, saturated, and cosmetic-corrected pixel classification is left for
  S2-Gate 5.
- Warp marks invalid coverage as `WARP_EDGE`; richer interpolation footprint
  diagnostics are later work.
- Local normalization marks invalid source/reference overlap as
  `LOCAL_NORMALIZATION_EXCLUDED`; continuous LN masking is a later gate.
- Resident CUDA does not yet emit the same DQ artifact family.

## Next Step

Proceed to S2-Gate 5: robust calibration completion, including robust master
frames, explicit dark/bias semantics, flat normalization/floor reporting,
pedestal, overscan/trim first pass, and cosmetic correction first pass using the
formal DQ contract.

## Clean-Room / Independence Status

This gate added project-owned DQ bitfield artifacts and summaries derived from
GLASS pipeline requirements. No proprietary PixInsight/WBPP/PJSR source code was
read, copied, summarized, or modified.
