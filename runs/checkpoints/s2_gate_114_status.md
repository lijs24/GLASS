# S2-Gate 114 Status: Agreement-Threshold Sweep Dimension

## Gate

S2-Gate 114: Agreement-Threshold Sweep Dimension.

## Completed Content

- Extended resident sweep variants with:
  - `triangle_min_agreement_score`
  - `triangle_agreement_rms_scale`
- Added benchmark CLI dimensions:
  - `--triangle-min-agreement-scores`
  - `--triangle-agreement-rms-scales`
- Encoded agreement dimensions in variant ids with `agr*` and `agrs*` suffixes.
- Emitted matching `glass run` options:
  - `--resident-triangle-min-agreement-score`
  - `--resident-triangle-agreement-rms-scale`
- Preserved existing behavior when dimensions are omitted or set to `inherit`.
- Updated Phase 2 gate documentation and algorithm-source audit notes.

## Commands Run

- `python -m ruff check src/glass/report/resident_sweep.py benchmarks/bench_resident_prefetch_sweep.py tests/test_benchmarks.py`
- `python -m pytest -q tests/test_benchmarks.py::test_bench_resident_prefetch_sweep_dry_run_registration_grid`
- `python benchmarks/bench_resident_prefetch_sweep.py --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_114_agreement_sweep_dimension --common-run-args-from-command C:\glass_runs\phase2_s2_gate_110_grid_shape_sweep\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_fcbase_g28x16_gt2_sep96\run_command.txt --frame-gate-from-contract benchmarks\phase2_m38_h_200_contract.json --compare-from-contract benchmarks\phase2_m38_h_200_contract.json --prefetch-frames 16 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes queued --triangle-fast-coarse-modes inherit --triangle-coarse-strides inherit --triangle-final-strides inherit --star-max-candidates inherit --star-grid-cols inherit --star-grid-rows inherit --triangle-grid-top-per-cell inherit --triangle-nms-scan-candidates inherit --triangle-nms-min-separation-px inherit --triangle-min-agreement-scores inherit,0.05,0.1 --triangle-agreement-rms-scales 200 --dry-run`
- `python -m ruff check .`
- `python -m pytest -q`
- Native CUDA build through Visual Studio developer environment:
  `cmake --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel`
- `glass doctor --json C:\glass_runs\phase2_s2_gate_114_agreement_sweep_dimension\doctor.json`

## Test Result

- Focused tests: passed.
- Full test suite: `317 passed in 15.51s`.
- Ruff: passed.
- Native CUDA build: passed, `ninja: no work to do`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_114_doctor.json`.

## Real-Data Dry-Run Artifact

- Artifact root:
  `C:\glass_runs\phase2_s2_gate_114_agreement_sweep_dimension`
- Summary JSON:
  `C:\glass_runs\phase2_s2_gate_114_agreement_sweep_dimension\resident_prefetch_sweep_summary.json`
- Summary Markdown:
  `C:\glass_runs\phase2_s2_gate_114_agreement_sweep_dimension\resident_prefetch_sweep_summary.md`
- Analysis JSON:
  `C:\glass_runs\phase2_s2_gate_114_agreement_sweep_dimension\resident_prefetch_sweep_analysis.json`
- Variant count: `3`.
- Dry run: `True`.
- Variant ids:
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agrs200`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agr0p05_agrs200`
  - `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agr0p1_agrs200`
- Frame gate: enabled, `planned_count=3`.
- Compare gate: enabled, `planned_count=3`.

## Known Limitations

- This gate only plans agreement-threshold sweeps; it does not execute or
  promote a threshold.
- The dry-run artifact proves command generation and gate metadata, not
  numerical image agreement.
- The `inherit` threshold variant with `agrs200` changes only the explicit RMS
  scale argument, which matches the current default and remains audit-only.

## Next Step

Execute a small bounded 200-light agreement-threshold sweep using the new
dimensions, parse candidate audits for each variant, and require frame-count,
guardrail, and strict image-compare gates before considering any threshold
promotion.

## Clean-Room Compliance

Compliant. This gate only changed GLASS-owned sweep orchestration and generated
GLASS-owned dry-run artifacts from existing benchmark command files and
contracts. It did not read or rely on external proprietary implementation
source and did not modify input image directories.
