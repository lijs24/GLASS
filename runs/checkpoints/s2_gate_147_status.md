# S2-Gate 147 Status - Tile-Local Frame-Family Search

## Gate

S2-Gate 147: tile-local frame-family search.

## Completed

- Added `glass tile-local-frame-family-search`.
- Implemented clean-room scoring for contiguous sorted frame windows using
  GLASS resident contribution artifacts and residual tile manifests.
- Reused the tile-local proposal scale, residual-stat, multiplier bounds, and
  saturation diagnostics so the search is comparable with S2-Gates 145-146.
- Added focused unit and CLI smoke coverage.
- Ran the command on the S2-Gate 144 new-region contribution artifact for
  1/3/5/11-frame windows.
- Wrote both a top-ranked artifact and an all-candidates artifact.
- Updated Phase 2 planning and algorithm-source documentation.

## Real-Data Artifacts

- Top-ranked frame-family search JSON:
  `C:\glass_runs\phase2_s2_gate_147_frame_family_search\new_region_frame_family_search.json`
- Top-ranked frame-family search Markdown:
  `C:\glass_runs\phase2_s2_gate_147_frame_family_search\new_region_frame_family_search.md`
- All-candidates frame-family search JSON:
  `C:\glass_runs\phase2_s2_gate_147_frame_family_search\new_region_frame_family_search_all.json`
- Doctor report:
  `runs\checkpoints\s2_gate_147_doctor.json`

## Real-Data Results

- Candidate count: `756`.
- Top candidate: `F000100-F000110`.
- Top window size: `11`.
- Top total absolute residual reduction: `0.0003515000452261885`.
- Top mean absolute residual after: `0.005742790954133888`.
- Top clamped fraction: `1.0`.
- Top applied-to-required boost ratio mean: `0.018736000426309976`.

Best candidates by window size from the all-candidates artifact:

| window | best candidate | total reduction | mean abs after | toward tiles | applied/required boost ratio mean |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `F000105` | `3.3682821581192124e-05` | `0.005782518107089512` | `8` | `0.0018187694819196431` |
| 3 | `F000104-F000106` | `9.940106655828562e-05` | `0.005774303326467375` | `8` | `0.00534725682003528` |
| 5 | `F000102-F000106` | `0.00016308604940240556` | `0.0057663427036118604` | `8` | `0.008748292432110387` |
| 11 | `F000100-F000110` | `0.0003515000452261885` | `0.005742790954133888` | `8` | `0.018736000426309976` |

The result says the F000100-F000110 focus group is not arbitrary; it is the
best visible frame-family explanation in this artifact. It also says the
explanation is weak under the current bounded multiplier model, because even
the best 11-frame window leaves the same small S2-Gate 145 residual reduction.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_tile_local_frame_family_search.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src\glass\report\tile_local_frame_family_search.py src\glass\cli.py tests\test_tile_local_frame_family_search.py tests\test_cli_smoke.py
.\.venv\Scripts\glass.exe tile-local-frame-family-search --contribution C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json --tile-pack C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.json --out C:\glass_runs\phase2_s2_gate_147_frame_family_search\new_region_frame_family_search.json --markdown C:\glass_runs\phase2_s2_gate_147_frame_family_search\new_region_frame_family_search.md --residual-stat tail_signed_mean --min-multiplier 0.0 --max-multiplier 2.0 --glass-scale 8.764434957115609e-06 --top-n 30
.\.venv\Scripts\glass.exe tile-local-frame-family-search --contribution C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json --tile-pack C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.json --out C:\glass_runs\phase2_s2_gate_147_frame_family_search\new_region_frame_family_search_all.json --residual-stat tail_signed_mean --min-multiplier 0.0 --max-multiplier 2.0 --glass-scale 8.764434957115609e-06 --top-n 0
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_147_doctor.json
```

## Test Results

- Focused pytest: `3 passed in 0.91s`.
- Full pytest: `376 passed in 20.46s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_147_doctor.json`.

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

- This gate is a summary search only. It does not write image pixels and does
  not prove physical causality.
- Frame windows are sorted by available GLASS frame ids; they are diagnostic
  windows, not necessarily acquisition-session metadata groups.
- Scores use tile-level residual/contribution means and bounded multipliers,
  not a native per-pixel solve.
- Local normalization remains disabled in this benchmark path.

## Next Step

S2-Gate 148 should move away from hunting alternate frame families and examine
why the residual magnitude is much larger than the available bounded
frame-family contribution. The most useful next diagnostic is a residual-source
split between low/high rejection maps, coverage, registration agreement, and
local background/scale mismatch for the same top new-region tiles.

## Clean-Room Compliance

Compliant. This gate consumes GLASS resident contribution and residual
candidate JSON artifacts only. No proprietary implementation source was read,
copied, summarized, or reworked.
