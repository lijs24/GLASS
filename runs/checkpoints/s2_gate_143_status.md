# S2-Gate 143 Status - Residual Tile Candidate Mining

## Gate

S2-Gate 143: residual tile candidate mining.

## Completed

- Added `glass residual-tile-candidates`.
- The command merges one or more `compare-outliers` artifacts into a
  tile-pack-like residual candidate manifest.
- Candidates are ranked by an explicit tail metric, filtered by minimum tail
  pixels/fraction, and greedily de-overlapped by default.
- Known tile packs can be supplied only for overlap labeling, so previously
  studied F000100-F000110 regions remain visible and are not misrepresented as
  new discoveries.
- Added focused tests for non-overlap selection, known-overlap labeling, and
  CLI JSON/Markdown output.
- Updated Phase 2 planning and algorithm-source documentation.
- Generated a real 200-light candidate manifest from the existing outlier
  audits.

## Real-Data Artifacts

- Residual candidate manifest:
  `C:\glass_runs\phase2_s2_gate_143_residual_candidates\residual_tile_candidates.json`
- Residual candidate Markdown:
  `C:\glass_runs\phase2_s2_gate_143_residual_candidates\residual_tile_candidates.md`
- Doctor report:
  `runs\checkpoints\s2_gate_143_doctor.json`

## Inputs

- Outlier audit:
  `C:\glass_runs\phase2_s2_gate_120_compare_outliers\agr0p5_outliers.json`
- Outlier audit:
  `C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005_outliers.json`
- Outlier audit:
  `C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_outliers.json`
- Known tile pack:
  `C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json`

## Real-Data Results

- Source outlier audit count: `3`.
- Raw candidate count after filters: `48`.
- Selected non-overlapping candidate tiles: `12`.
- Selected tiles overlapping the known Gate121 tile pack: `7`.
- Selected new-region tiles: `5`.
- Dropped due to selected-tile overlap: `22`.
- Dropped due to max-tile limit: `14`.
- Top score: `102395.0`.
- Recommendation: `capture_resident_contributions_for_selected_tiles`.
- New-region selected extents:
  - `{'x0': 5136, 'y0': 3600, 'x1': 5648, 'y1': 4112}`
  - `{'x0': 7184, 'y0': 3088, 'x1': 7696, 'y1': 3600}`
  - `{'x0': 7696, 'y0': 3088, 'x1': 8208, 'y1': 3600}`
  - `{'x0': 7184, 'y0': 3600, 'x1': 7696, 'y1': 4112}`
  - `{'x0': 2576, 'y0': 4112, 'x1': 3088, 'y1': 4624}`

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_residual_tile_candidates.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src\glass\report\residual_tile_candidates.py tests\test_residual_tile_candidates.py src\glass\cli.py
.\.venv\Scripts\glass.exe residual-tile-candidates --outlier-audit C:\glass_runs\phase2_s2_gate_120_compare_outliers\agr0p5_outliers.json --outlier-audit C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005_outliers.json --outlier-audit C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_outliers.json --known-tile-pack C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json --out C:\glass_runs\phase2_s2_gate_143_residual_candidates\residual_tile_candidates.json --markdown C:\glass_runs\phase2_s2_gate_143_residual_candidates\residual_tile_candidates.md --max-tiles 12 --min-tail-pixels 3000 --prefer tail_pixels
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_143_doctor.json
```

## Test Results

- Focused pytest: `3 passed`.
- Full pytest: `374 passed in 21.09s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_143_doctor.json`.

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

- This gate mines existing outlier audit JSON only; it does not read image
  pixels or generate FITS/PNG tile cutouts.
- The selected candidate manifest identifies where to run resident contribution
  capture next; it is not a tile-local policy and does not prove that any
  correction is safe.
- The top candidates are still dominated by the Gate120 baseline outlier audit
  because it has the largest tail-pixel counts; later gates may compare
  alternate rankings such as tail fraction or tail absolute mean.

## Next Step

S2-Gate 144 should run `resident-tile-contribution` on the Gate143 candidate
manifest, prioritizing the five new-region tiles. That will determine whether
the F000100-F000110 frame family also explains the newly mined residual regions
or whether a different frame family/policy is needed.

## Clean-Room Compliance

Compliant. This gate consumes GLASS compare-outlier JSON artifacts and known
GLASS tile-pack manifests only. No proprietary implementation source was read,
copied, summarized, or reworked.
