# S2-Gate 144 Status - New-Region Resident Contribution Capture

## Gate

S2-Gate 144: new-region resident contribution capture.

## Completed

- Extended `glass residual-tile-candidates` with
  `--known-overlap-mode include|exclude|only`.
- Added test coverage for excluding known-overlap tiles.
- Generated a new-region-only candidate manifest from the Gate143 outlier
  sources while excluding regions overlapping the Gate121 known tile pack.
- Ran `glass resident-tile-contribution` on the new-region manifest using the
  200-light resident CUDA benchmark run.
- Captured all 193 positive-weight frames across 8 new residual tiles and
  replayed winsorized-sigma contribution diagnostics.
- Updated Phase 2 planning and algorithm-source documentation.

## Real-Data Artifacts

- New-region candidate manifest:
  `C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.json`
- New-region candidate Markdown:
  `C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.md`
- Resident contribution artifact:
  `C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json`
- Resident contribution Markdown:
  `C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.md`
- Doctor report:
  `runs\checkpoints\s2_gate_144_doctor.json`

## Real-Data Results

- New-region manifest:
  - Raw candidate count after known-overlap filtering: `22`.
  - Selected non-overlapping new-region tiles: `8`.
  - Known-overlap selected tiles: `0`.
  - Dropped overlaps: `8`.
- Resident contribution capture:
  - Selected positive-weight frames: `193`.
  - Tile count: `8`.
  - Focus range: `F000100` through `F000110` (`11` frames).
  - Control frames: `10` neighboring frames.
  - Rejection replay: `winsorized_sigma`.
  - Interpolation: `lanczos3`.
  - Calibration total: `13.593834299999992 s`.
  - Capture elapsed: `109.70733329979703 s`.
- Focus/control contribution:
  - Focus tile normalized contribution mean: `5.013158962130547`.
  - Control tile normalized contribution mean: `1.6990089239552617`.
  - Focus minus control: `3.314150038175285`.
  - Focus normalized delta contribution mean: `0.4557417238300497`.
  - Control normalized delta contribution mean: `0.16990089239552617`.
  - Focus minus control normalized delta mean: `0.28584083143452355`.
  - Focus rejected fraction: `0.03687884590842507`.
  - Control rejected fraction: `0.0045989990234375`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_residual_tile_candidates.py tests\test_cli_smoke.py::test_cli_help_commands
.\.venv\Scripts\ruff.exe check src\glass\report\residual_tile_candidates.py tests\test_residual_tile_candidates.py src\glass\cli.py
.\.venv\Scripts\glass.exe residual-tile-candidates --outlier-audit C:\glass_runs\phase2_s2_gate_120_compare_outliers\agr0p5_outliers.json --outlier-audit C:\glass_runs\phase2_s2_gate_128_motion_weighting\motion_cluster_t16_min005_outliers.json --outlier-audit C:\glass_runs\phase2_s2_gate_129_frame_weight_proposal\proposal_control_ratio_outliers.json --known-tile-pack C:\glass_runs\phase2_s2_gate_121_tile_pack\agr0p5_top_tiles\tile_pack_manifest.json --out C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.json --markdown C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.md --max-tiles 8 --min-tail-pixels 3000 --prefer tail_pixels --known-overlap-mode exclude
.\.venv\Scripts\glass.exe resident-tile-contribution --tile-pack C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_tile_candidates.json --run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200 --out C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.json --markdown C:\glass_runs\phase2_s2_gate_144_new_region_contribution\new_region_resident_contribution.md --filter H --frame-strategy frame_id --max-frames 0 --max-tiles 0 --rejection winsorized_sigma --focus-range-start F000100 --focus-range-end F000110 --control-before 5 --control-after 5
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_144_doctor.json
```

## Test Results

- Focused pytest: `3 passed`.
- Full pytest: `374 passed in 24.60s`.
- Ruff: `All checks passed`.
- Doctor: passed and wrote `runs\checkpoints\s2_gate_144_doctor.json`.

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

- This gate is diagnostic. It does not generate or apply a new tile-local
  policy.
- Resident contribution capture downloads selected post-warp tiles and replays
  rejection diagnostics on CPU; it is not a byte-level trace inside the native
  integration kernel.
- Local normalization remains disabled in this benchmark path.

## Next Step

S2-Gate 145 should run `tile-local-policy-proposal` and
`tile-local-policy-replay` on the new-region contribution artifact. The key
question is whether the same F000100-F000110 boost/downweight logic improves
these broader regions or whether the policy must be spatially/family-specific.

## Clean-Room Compliance

Compliant. This gate consumes GLASS residual candidate, run, and CUDA capture
artifacts only. No proprietary implementation source was read, copied,
summarized, or reworked.
