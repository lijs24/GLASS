# S2-Gate 661 Status: Star-Protected Inline Cosmetic Source-DQ Baseline

## Gate

- Gate: S2-Gate 661.
- Status: green.
- Purpose: establish a star/catalog-protected CPU source-DQ baseline and opt-in resident mode before porting the detector to the high-throughput resident CUDA path.

## Completed

- Added `glass.cpu.cosmetic.detect_star_protected_cosmetic_defects`.
- Added `glass.cpu.cosmetic.star_protection_mask`.
- Added `glass.engine.resident_source_dq.source_invalid_mask_from_star_protected_inline_cosmetic`.
- Added opt-in `--resident-inline-source-dq cosmetic_star` for `glass run` and `glass audit`.
- Wired `cosmetic_star` into resident source-DQ strategy and resident CUDA run artifacts.
- Added synthetic result tests proving a compact PSF-like star core is protected while a separate isolated hot pixel remains masked.
- Added a focused tiny resident CUDA smoke test proving `cosmetic_star` executes through the resident path and records strategy/artifact/timing fields.
- Updated Phase 2 docs, validation notes, and algorithm-source independence log.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\cpu\cosmetic.py src\glass\engine\resident_source_dq.py src\glass\engine\resident_source_dq_strategy.py src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_source_dq.py tests\test_resident_source_dq_strategy.py tests\test_cli_smoke.py tests\test_resident_cuda_run.py

.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq.py tests\test_resident_source_dq_strategy.py tests\test_cli_smoke.py::test_run_resident_inline_source_dq_accepts_star_protected_mode tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_star_protected_cosmetic_source_dq

.\.venv\Scripts\python.exe -m pytest -q

nvidia-smi --query-gpu=name,compute_cap,memory.total,driver_version --format=csv,noheader
```

## Test Results

- Ruff: `All checks passed`.
- Focused tests: `23 passed in 1.18s`.
- Full pytest: `1391 passed in 61.73s`.

## CUDA

- CUDA available: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- Total VRAM reported by `nvidia-smi`: `97887 MiB`.
- Driver: `596.21`.

## Validation Artifact

- This gate uses focused synthetic validation plus a tiny resident CUDA smoke test.
- No new 200-light heavy A/B run was launched for this gate because the gate establishes the CPU science contract and resident mode plumbing, not the final GPU detector.
- Latest real 200-light mainline acceptance remains Gate660:
  `C:\glass_runs\phase2_s2_gate660_active_registered_source_dq\runs_20260625_223412\active_registered_conservative_policy_strict`.

## Known Limitations

- `cosmetic_star` is CPU-controlled and opt-in.
- The detector is not yet resident CUDA-native.
- The star protection defaults are project-defined conservative guards and still require 200-light real-data impact validation after GPU porting.
- Default resident source-DQ remains `off`; no default science route was promoted.

## Next Step

- Implement the resident CUDA version of the star-protected source-DQ detector:
  keep star catalogs/candidate masks resident, apply protected candidate masks on device, then run the M38 200-light A/B against Gate660/Gate659 and the black-box reference.

## Clean-Room Compliance

- This gate uses GLASS-owned CPU star detection, GLASS DQ flags, GLASS resident artifacts, and GLASS synthetic tests.
- No external or proprietary implementation source was inspected, copied, summarized, or reworked.
- No input data directory was modified.
