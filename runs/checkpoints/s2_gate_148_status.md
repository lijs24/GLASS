# S2-Gate 148 Status - Tile-Local Residual Source Audit

## Gate

S2-Gate 148: tile-local residual source audit.

## Completed

- Added `glass tile-local-residual-source-audit`.
- Implemented clean-room aggregation over GLASS resident contribution,
  residual tile-pack, and frame-family search JSON artifacts.
- Summarized coverage fraction, high/low rejection map means,
  focus-vs-control rejection excess, top frame-family explained fraction, and
  routing recommendation.
- Added focused unit and CLI smoke coverage.
- Ran the audit on the S2-Gate 144 new-region contribution artifact using the
  S2-Gate 147 frame-family search artifact.
- Updated Phase 2 planning and algorithm-source documentation.

## Real-Data Artifacts

- Residual-source audit JSON:
  `C:\glass_runs\phase2_s2_gate_148_residual_source\new_region_residual_source_audit.json`
- Residual-source audit Markdown:
  `C:\glass_runs\phase2_s2_gate_148_residual_source\new_region_residual_source_audit.md`
- Doctor report:
  `runs\checkpoints\s2_gate_148_doctor.json`

## Real-Data Results

- Recommendation: `prioritize_rejection_registration_diagnostics`.
- Coverage-below-threshold tiles: `0`.
- Focus high-rejection-excess tiles: `8`.
- Top frame-family candidate: `F000100-F000110`.
- Top frame-family explained fraction: `0.007592805841608405`.
- Coverage fraction mean stats:
  - Min: `0.9946988555433837`.
  - Mean: `0.995176483312419`.
  - Max: `0.9956305904091949`.
- High rejection map mean stats:
  - Min: `0.6534614562988281`.
  - Mean: `0.6991009712219238`.
  - Max: `0.775543212890625`.
- Low rejection map mean stats:
  - Min: `0.18857574462890625`.
  - Mean: `0.23183774948120117`.
  - Max: `0.2648658752441406`.
- Focus high-rejection excess stats:
  - Min: `0.027336502075195314`.
  - Mean: `0.03238433491099965`.
  - Max: `0.034730807217684664`.

The audit rules out a broad coverage/valid-mask explanation for the new-region
residual tiles. The best frame-family explanation is still F000100-F000110,
but it explains less than `1%` of the total residual under the bounded
tile-level model. All eight tiles show focus high-rejection excess, so the next
work should prioritize rejection/registration interaction diagnostics instead
of simply boosting that frame family.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_residual_source_audit.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_residual_source_audit.py src\glass\cli.py tests\test_tile_local_residual_source_audit.py tests\test_cli_smoke.py
.\.venv\Scripts\glass.exe tile-local-residual-source-audit --contribution C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json --tile-pack C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.json --frame-family-search C:\glass_runs\phase2_s2_gate_147_frame_family_search\new_region_frame_family_search.json --out C:\glass_runs\phase2_s2_gate_148_residual_source\new_region_residual_source_audit.json --markdown C:\glass_runs\phase2_s2_gate_148_residual_source\new_region_residual_source_audit.md --residual-stat tail_signed_mean --high-rejection-excess-threshold 0.01 --min-coverage-fraction 0.95
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_148_doctor.json
```

## Test Results

- Focused pytest after fix: `3 passed in 0.63s`.
- Full pytest: `378 passed in 22.15s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_148_doctor.json`.

## CUDA Status

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Recommended package: `cuda`.

## Known Limitations

- This gate reads GLASS diagnostic JSON only; it does not read image pixels or
  run native integration.
- The recommendation is a routing diagnostic, not proof of root cause.
- Frame-family explanatory fraction still uses bounded tile-level summaries,
  not a per-pixel native solve.
- Local normalization remains disabled in this benchmark path.

## Next Step

S2-Gate 149 should inspect the same residual tiles at frame level, ranking
focus and neighboring frames by high rejection fraction, accepted fraction,
triangle agreement score, registration RMS, NCC, and agreement downweight. The
goal is to determine whether the high-rejection excess is tied to a specific
registration-quality pattern before changing weighting or rejection behavior.

## Clean-Room Compliance

Compliant. This gate consumes GLASS JSON artifacts only. No proprietary
implementation source was read, copied, summarized, or reworked.
