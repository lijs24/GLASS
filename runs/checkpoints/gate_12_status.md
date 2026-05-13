# Gate 12 Status: End-to-End CUDA WBPP-like Pipeline

- Gate: 12
- Date: 2026-05-13
- Status: completed
- Commit evidence:
  - `44637ef gate-12: add resident audit entry`
  - `15cbace gate-12: report resident strategy fields`
  - `876359c gate-12: add resident end-to-end benchmark option`
  - `b8c1d7f gate-12: expose resident audit registration tuning`

## Completed

- `glass audit` supports scan -> plan -> run -> report for executable plans.
- The tile-mode pipeline covers calibration, quality, registration, warp,
  local normalization, integration, resume behavior, and reports.
- The resident CUDA path supports a high-VRAM end-to-end benchmark mode using a
  VRAM-resident calibrated stack.
- Resident CUDA mode records strategy fields in `resident_artifacts.json` and
  report output, including registration mode, warp interpolation, local
  normalization, weighting, rejection, timing, and memory estimates.
- Resident CUDA audit/run options expose the registration tuning used by the
  final real-data benchmark.
- CPU/CUDA small-sample tests and real M38 resident benchmark evidence both
  exist.

## Representative Commands

```powershell
.\.venv\Scripts\glass synthetic --out runs\gate_12_synth\source --frames 5 --width 48 --height 48 --filter H --known-shift
.\.venv\Scripts\glass audit --root runs\gate_12_synth\source --out runs\gate_12_synth\cuda_audit --backend cuda --tile-size 12 --local-normalization on --integration-weighting none --integration-rejection none
.\.venv\Scripts\glass resume --run runs\gate_12_synth\cuda_audit
.\.venv\Scripts\glass audit --root runs\gate_12_synth\source --out runs\gate_12_synth\cpu_audit --backend cpu --tile-size 12 --local-normalization on --integration-weighting none --integration-rejection none
.\.venv\Scripts\glass compare --glass runs\gate_12_synth\cuda_audit\integration\master_H.fits --reference runs\gate_12_synth\cpu_audit\integration\master_H.fits --out runs\gate_12_synth\cuda_vs_cpu_compare.html
.\.venv\Scripts\python.exe -m pytest -q
```

## Latest Test Result

- Latest full suite after checkpoint refresh: `178 passed in 7.95s`.

## CUDA Availability

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Native backend: true.

## Artifacts

Synthetic Gate 12 artifacts:

- `runs/gate_12_synth/source/`
- `runs/gate_12_synth/cuda_audit/manifest.json`
- `runs/gate_12_synth/cuda_audit/processing_plan.json`
- `runs/gate_12_synth/cuda_audit/run_state.json`
- `runs/gate_12_synth/cuda_audit/report.html`
- `runs/gate_12_synth/cuda_audit/integration/master_H.fits`
- `runs/gate_12_synth/cuda_audit/integration/weight_map_H.fits`
- `runs/gate_12_synth/cuda_audit/integration/coverage_map_H.fits`
- `runs/gate_12_synth/cuda_audit/integration/low_rejection_H.fits`
- `runs/gate_12_synth/cuda_audit/integration/high_rejection_H.fits`
- `runs/gate_12_synth/cpu_audit/integration/master_H.fits`
- `runs/gate_12_synth/cuda_vs_cpu_compare.html`
- `runs/gate_12_synth/cuda_vs_cpu_compare.json`

Real resident CUDA artifacts:

- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\run_timing.json`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\resident_artifacts.json`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_master_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_coverage_map_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_low_rejection_map_H.fits`
- `C:\glass_runs\final_m38_h_200\glass_resident_triangle_193_wbpp_failed_excluded_lanczos3\integration\resident_high_rejection_map_H.fits`

## Known Limitations

- Resume no-op works for completed integration results; checksum-based
  per-stage skipping remains future hardening.
- Resident CUDA is a high-VRAM execution strategy, not the replacement for the
  tile/out-of-core path.
- The fastest validated real-data parity run disables local normalization.
- GLASS remains WBPP-like and clean-room; exact PixInsight/WBPP algorithmic
  equivalence is not claimed.

## Next Step

- Gate 13 remains the comparison/acceptance evidence layer, now backed by
  `glass speedup-summary` and `glass acceptance-audit`.

## Clean-room Compliance

- No official PixInsight WBPP/PJSR source was read, copied, summarized, or
  modified.
- Input data directories were not modified.
