# Gate 04 Resident Run Status

## Gate

Formal `gpwbpp run` support for the full-VRAM resident CUDA calibration plus
mean integration path.

## Completed

- Added `--memory-mode resident` to `gpwbpp run`.
- Added `gpwbpp.engine.resident_cuda` as the formal resident execution path.
- Resident mode aggregates lights by filter/shape so the M38 H run uses one
  200-frame calibrated stack instead of per-frame stacks.
- Resident mode aggregates calibration frames by same shape/filter, using all
  selected M38 calibration frames: 20 bias, 20 dark, and 20 flat.
- Resident mode writes:
  - `resident_artifacts.json`
  - `integration_results.json`
  - `run_timing.json`
  - `run_state.json`
  - final master FITS
  - weight map FITS
- Added a CUDA CLI smoke test for the resident run mode.

## Commands

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py tests/test_cuda_resident_stack.py tests/test_cli_smoke.py
.venv\Scripts\python.exe -m gpwbpp.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none
.venv\Scripts\python.exe -m gpwbpp.cli report --run C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run --out C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\report.html
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Targeted resident CLI tests: 5 passed in 0.31 s.
- Full test suite: 66 passed in 5.31 s.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Total VRAM: 97887 MiB reported by `nvidia-smi`.

## Real Benchmark

- Dataset: M38 H mono.
- Input staged on C:.
- Lights: 200.
- Bias: 20.
- Dark: 20.
- Flat: 20.
- Formal resident run total: 58.981 s.
- Light read/upload/calibrate: 38.152 s.
- Resident mean integration: 0.114 s.
- Resident base VRAM: 46.85 GiB.
- Estimated peak VRAM: 47.31 GiB.
- WBPP black-box total on the same staged dataset: 1092.541 s.
- Speedup of this formal resident gate path versus WBPP black-box total: 18.52x.

## Artifacts

- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\resident_artifacts.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\integration_results.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\run_timing.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\run_state.json`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\integration\resident_master_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\integration\resident_weight_map_H.fits`
- `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\report.html`
- `C:\gpwbpp_runs\final_m38_h_200\formal_resident_vs_wbpp_summary.md`
- `C:\gpwbpp_runs\final_m38_h_200\formal_resident_vs_wbpp_summary.json`

## Known Limitations

- This gate path covers high-VRAM calibration plus mean integration.
- Registration, warp, Local Normalization, rejection maps, autocrop, and
  WBPP-equivalent weighting are intentionally not part of this resident path yet.
- The resident path writes a weight map, but coverage and rejection maps are null
  because no registration/rejection is applied in this gate.
- It is a formal `gpwbpp run` mode now, but still a capability flag rather than
  the complete WBPP-like pipeline.

## Next Step

Extend the same staged-residency model to registration/warp, then integrate
coverage maps and rejection maps without materializing every historical layer at
once.

## Clean Room

Compliant. PixInsight/WBPP was used only as a black-box timing baseline. No
official WBPP/PJSR source was read or copied.
