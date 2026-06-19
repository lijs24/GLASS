# S2-Gate 456 Status: Resident CUDA Inline Source-DQ Thresholds

## Gate

- Gate: S2-Gate 456
- Scope: Opt-in resident CUDA inline source-DQ threshold detector plus 200-light audit-map regression.
- Status: passed
- Date: 2026-06-20 local

## Completed Work

- Added native CUDA kernel `glass_apply_cosmetic_threshold_mask_f32_kernel`.
- Added `ResidentCalibratedStack.apply_cosmetic_threshold_mask_frame`, returning hot/cold/nonfinite counts, timing, and `mask_upload_s=0`.
- Exposed the new native method through `glass_cuda.ResidentCalibratedStack`.
- Added `--resident-inline-source-dq cosmetic_cuda` to `glass run` and `glass audit`.
- Added scalar threshold helpers using the same median/MAD fallback-std rule as the CPU cosmetic baseline.
- Threaded `cosmetic_cuda` through resident batch and per-frame calibration paths.
- Updated source-DQ summaries, strategy artifacts, and resident I/O artifacts with native method, detector execution, and threshold-source provenance.
- Kept `cosmetic` CPU-mask mode and default `off` mode unchanged.

## Real 200-Light Results

- Primary accepted run: `C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620`
- Minimal default timing run: `C:\glass_runs\phase2_s2_gate_456_200\contract_parity_20260620`
- Input: M38 H-alpha 200 lights, 20 bias, 20 dark, 20 flat.
- Resident inline source-DQ mode: `off` for real default-path regression.
- Audit-map GLASS elapsed: `31.352762 s`.
- Minimal default GLASS elapsed: `22.352832 s`.
- WBPP black-box elapsed: `1092.541 s`.
- Speedup vs WBPP, audit-map run: `34.846723x`.
- Integrated frames: `193/200`.
- Zero-weight quality-rejected frames: `7`.
- Compare:
  - shape match: true
  - coverage fraction: `0.9608153775`
  - RMS diff: `0.0016827200`
  - P99 absolute diff: `0.0004569261`
- Acceptance audit: passed, zero failed checks.

## Commands Run

- `cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native'`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq.py tests\test_cuda_resident_stack.py::test_resident_stack_apply_cosmetic_threshold_mask_frame_excludes_hot_cold_nonfinite_samples tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_applies_inline_cosmetic_cuda_source_dq_without_mask_upload`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_source_dq.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620 --backend cuda --until-stage integration --memory-mode resident ... --resident-output-maps audit`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli compare --glass C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\s2_gate_456_compare.html ...`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli resident-calibration-contract --run C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620 --out C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\resident_calibration_contract_s2_gate_456.json --fail-on-failed`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli resident-result-contract --run C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620 --out C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\resident_result_contract_s2_gate_456.json --pixel-verify --fail-on-failed`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli pipeline-contract --run C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620 --out C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\pipeline_contract_s2_gate_456.json --pixel-verify --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\resident_calibration_contract_s2_gate_456.json`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli stack-engine-contract --run C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620 --out C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\stack_engine_contract_s2_gate_456.json --expected-integration-engine cuda_resident_stack --resident-calibration-contract-json C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\resident_calibration_contract_s2_gate_456.json --resident-result-contract-json C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\resident_result_contract_s2_gate_456.json`
- `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m glass.cli acceptance-audit --manifest C:\gpwbpp_runs\final_m38_h_200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\s2_gate_456_compare.json --out C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\phase2_contract_acceptance_audit_s2_gate_456.json --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\pipeline_contract_s2_gate_456.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\stack_engine_contract_s2_gate_456.json`
- `.\.venv\Scripts\python.exe -m ruff check cpp src\glass\engine\resident_source_dq.py src\glass\engine\resident_source_dq_strategy.py src\glass\engine\resident_cuda.py src\glass\cli.py src\glass_cuda.py tests\test_resident_source_dq.py tests\test_cuda_resident_stack.py tests\test_resident_cuda_run.py`

## Test Results

- Focused source-DQ/CUDA/CLI pytest: `10 passed`.
- Resident/source-DQ regression pytest: `110 passed`.
- Full pytest: `1084 passed in 40.83 s`.
- Focused ruff: passed.

## Artifacts

- `runs/checkpoints/s2_gate_456_real_regression_summary.json`
- `runs/checkpoints/s2_gate_456_status.md`
- `C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\s2_gate_456_compare.json`
- `C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\s2_gate_456_compare.html`
- `C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\phase2_contract_acceptance_audit_s2_gate_456.json`
- `C:\glass_runs\phase2_s2_gate_456_200\contract_parity_audit_20260620\resident_source_dq_execution.json`

## CUDA Status

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97887 MiB.
- Driver: 596.21.
- CUDA toolkit used for native build: 13.2.

## Known Limitations

- `cosmetic_cuda` is opt-in and defaults to `off`.
- The per-pixel detector/application is CUDA resident, but scalar threshold statistics are still CPU median/MAD. A later gate should move median/MAD or robust threshold estimation to CUDA reductions.
- `cosmetic_cuda` currently expects host-visible numeric frame data for threshold preparation; raw-u16 GPU decode needs a future fully resident threshold-statistics path.
- The accepted real 200-light run used `resident_inline_source_dq=off` because enabling cosmetic source-DQ intentionally changes sample admission.

## Next Gate

- S2-Gate457 should move robust threshold statistics into resident CUDA reductions or batch the detector across resident frames, then run focused correctness and 200-light timing to measure whether source-DQ can stay entirely resident with no host mask or host threshold pass.

## Clean-Room Compliance

- Compliant. This gate used GLASS source, GLASS synthetic fixtures, GLASS-generated artifacts, and user-owned 200-light outputs.
- Original image directories remained read-only.
- No official PixInsight/WBPP/PJSR implementation source was read, copied, summarized, or modified.
