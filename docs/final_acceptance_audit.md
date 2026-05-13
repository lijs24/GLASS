# Final Acceptance Audit

Date: 2026-05-13

This audit records the current evidence for the user-requested GPWBPP
acceptance target. It is intentionally evidence-based: passing tests and
checkpoint files are treated as support, not as substitutes for checking the
actual benchmark artifacts.

## Objective Restatement

Core acceptance target:

- Build GPWBPP as a clean-room, installable, testable, resumable CUDA/WBPP-like
  astronomical preprocessing pipeline.
- Advance by Gates, with checkpoint files, tests, and Git commits.
- Run a real same-data comparison against PixInsight/WBPP.
- Use a significant mono target test: at least 200 light frames and at least 20
  frames in each calibration class.
- Show a clear GPWBPP speedup and verify the stacked result is consistent enough
  to rule out an obvious processing error.

This audit does not claim full PixInsight algorithmic equivalence. It also does
not treat optional Gate 14 or Phase B features as completed.

## Prompt-to-artifact Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Clean-room boundary | `docs/pixinsight_blackbox_reference.md`; Gate 13 checkpoints consume user-generated WBPP output only. | Met for current work |
| Dedicated project repo and branch | Git branch `gpwbpp-cuda-wbpp`; committed gate history through Gate 13. | Met |
| Virtual environment use | Commands use `.\.venv\Scripts\python.exe` and `.\.venv\Scripts\gpwbpp.exe`. | Met |
| Gate checkpoints | `runs/checkpoints/gate_00_status.md` through `runs/checkpoints/gate_13_status.md`, plus incremental Gate 8-13 status files. | Met through Gate 13 |
| Tests after gate work | Latest full suite: `176 passed in 8.07s`. | Met |
| CUDA optional and detectable | Capability/checkpoint records show native CUDA backend on NVIDIA RTX PRO 6000 Blackwell Workstation Edition. | Met |
| Out-of-core path | Tile/slab pipeline remains available; resident CUDA mode is explicitly a high-VRAM benchmark path. | Met for both modes |
| High-VRAM resident strategy | `resident_artifacts.json` and `integration_results.json` record `cuda_resident_stack`, estimated peak VRAM, and progressive resident outputs. | Met for benchmark |
| Synthetic/CPU baseline | Gate 2 and later CPU/GPU tests cover master frames, calibration, star detection, registration, warp, local normalization, and integration. | Met for baseline |
| Real comparison data scale | Final M38 manifest has 260 frames: 200 light, 20 bias, 20 dark, 20 flat. | Met |
| Same target/filter | Final dataset is `M38_H_200light_20bias_20dark_20flat`; all lights are H-alpha mono frames. | Met |
| Calibrations near in temperature/exposure | Manifest records 600s dark/light, gain 56, full 9600x6422 shape; temperatures cluster around -20 C. | Met for benchmark |
| WBPP black-box timing | `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json` records `1092.541 s`. | Met |
| GPWBPP timing | `run_timing.json` in the resident CUDA run records `111.94882199994754 s`. | Met |
| Speedup threshold | `gpwbpp speedup-summary` reports `9.75928982978054x` vs WBPP and threshold `2.0x` true. | Met |
| Same accepted frame set | GPWBPP weights 193 active frames and 7 zero-weight frames, matching WBPP FastIntegration's 193/200 accepted set. | Met |
| Result consistency | Coverage-masked compare at coverage >= 190 has shape match true, RMS `0.0017183155193652361`, p99 `0.00045279982034117025`, coverage fraction `0.9612859117097478`. | Met for acceptance |
| Diagnostic artifacts | Compare JSON/HTML, coverage map, rejection maps, weight map, timing JSON, and speedup summaries are present. | Met |
| No input directory mutation | Outputs are under `C:\gpwbpp_runs` and `runs\`; source directories are read-only inputs. | Met |
| PixInsight/WBPP source not used | Gate 13 status records black-box output/timing metadata only; no official WBPP/PJSR source was used. | Met |

## Current Acceptance Evidence

Final real-data run:

- Workspace: `C:\gpwbpp_runs\final_m38_h_200`
- GPWBPP run:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3`
- WBPP result:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`
- Compare artifact:
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_triangle_193_wbpp_failed_excluded_lanczos3\compare_vs_wbpp_fastintegration_scaled_coverage190.json`

Measured data:

- Frame counts: 200 light, 20 bias, 20 dark, 20 flat.
- WBPP elapsed: `1092.541 s`.
- GPWBPP elapsed: `111.94882199994754 s`.
- Speedup: `9.75928982978054x`.
- Active weighted frames: 193.
- Zero-weight/excluded frames: 7.
- Peak estimated VRAM: about `47.31 GiB`.
- Coverage-masked comparison fraction: `0.9612859117097478`.

## Commands Re-run During Audit

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Result:

```text
176 passed in 7.94s
```

The audit also inspected the real M38 manifest, processing plan, run timing,
integration results, coverage-masked compare JSON, and WBPP black-box result
JSON directly with a local Python script.

## Missing or Weakly Covered Items

- Optional Gate 14 PixInsight front-end is not implemented.
- Phase B advanced gates such as drizzle, OSC advanced workflows, mosaic, comet
  alignment, and richer astrometric integration are not implemented.
- The accepted real-data parity run disables local normalization; local
  normalization has separate Gate 10 CPU/GPU coverage but is not part of the
  fastest WBPP parity benchmark.
- GPWBPP does not claim exact WBPP algorithm identity. The current claim is a
  clean-room WBPP-like pipeline with a validated speedup and high-coverage
  output consistency on the selected data.

## Decision

The final real-data speedup target is achieved for the M38 H-alpha benchmark.
The broader engineering program should remain open for optional Gate 14 and
Phase B hardening. The project should not be described as a complete
drop-in PixInsight/WBPP clone.
