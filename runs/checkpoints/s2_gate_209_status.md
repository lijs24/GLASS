# S2-Gate 209 Status: Native Resident Calibration Artifact

- Gate: S2-Gate 209
- Status: green
- Date: 2026-06-18
- Scope: native resident CUDA calibration_artifacts.json and contracts

## Completed

- Added resident CUDA `calibration_artifacts.json` generation from `resident_artifacts.json`.
- Resident runs now write native calibration artifacts automatically after `resident_artifacts.json`.
- Added `glass resident-calibration-artifacts --run RUN [--out OUT]` for upgrading/auditing existing resident runs without reprocessing images.
- Recorded resident master bias/dark/flat surfaces with:
  - `backend= cuda_resident_stack`
  - cache path and stats
  - dark bias semantics
  - flat normalization and flat-floor semantics
  - embedded resident master-surface contracts
- Recorded each resident calibrated light as a `resident_in_vram` ledger row instead of pretending a calibrated FITS/DQ-mask pair exists on disk.
- Extended `glass pipeline-contract` with resident-native checks:
  - `resident_calibrated_lights_present`
  - `resident_calibrated_light_contract`
- Extended StackEngine contract handling so resident-native master rows count as CUDA resident StackEngine-family surfaces when their embedded contracts pass.
- Updated the 200-light benchmark contract to require native `resident_calibrated_light_contract` instead of the external resident calibration bridge check.

## Commands Run

- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\cli.py src\\glass\\engine\\resident_calibration_artifacts.py src\\glass\\engine\\resident_cuda.py src\\glass\\report\\pipeline_contract.py src\\glass\\report\\stack_engine_contract.py tests\\test_resident_calibration_artifacts.py tests\\test_pipeline_contract.py tests\\test_resident_cuda_run.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_resident_calibration_artifacts.py tests/test_pipeline_contract.py::test_pipeline_contract_accepts_resident_native_calibration_artifacts tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke tests/test_cli_smoke.py::test_cli_help_commands`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_pipeline_contract.py tests/test_stack_engine_contract.py tests/test_resident_calibration_contract.py tests/test_resident_calibration_artifacts.py tests/test_cli_smoke.py::test_cli_guardrails_generates_contracts_and_report`
- `.\\.venv\\Scripts\\glass.exe resident-calibration-artifacts --run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view"`
- `.\\.venv\\Scripts\\glass.exe pipeline-contract --run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --out runs\\checkpoints\\s2_gate_209_pipeline_contract.json --markdown runs\\checkpoints\\s2_gate_209_pipeline_contract.md --pixel-verify --pixel-verify-tile-size 2048`
- `.\\.venv\\Scripts\\glass.exe stack-engine-contract --run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --out runs\\checkpoints\\s2_gate_209_stack_engine_contract.json --markdown runs\\checkpoints\\s2_gate_209_stack_engine_contract.md --scope all --expected-integration-engine cuda_resident_stack --resident-result-contract-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\resident_result_contract.json" --require-default-ready`
- `.\\.venv\\Scripts\\glass.exe guardrails --run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --out-dir "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\guardrails" --expected-integration-engine cuda_resident_stack --resident-result-contract-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\resident_result_contract.json" --require-stack-default-ready --pixel-verify --pixel-verify-tile-size 2048`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_resident\\manifest.json" --glass-run "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view" --wbpp-result "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json" --compare-json "C:\\glass_runs\\phase2_s2_gate_181_default_runtime\\default_vs_reference.json" --benchmark-contract benchmarks\\phase2_m38_h_200_contract.json --contract-bundle "C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\guardrails\\acceptance_contract_bundle.json" --out runs\\checkpoints\\s2_gate_209_acceptance_real_native_artifact.json --markdown runs\\checkpoints\\s2_gate_209_acceptance_real_native_artifact.md --min-active-frames 190`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe doctor --allow-cpu-only --json runs\\checkpoints\\s2_gate_209_doctor.json`

## Test Results

- Focused tests: passed.
- Contract-focused tests: 26 passed.
- Full pytest: 496 passed in 26.59 s.
- Ruff: all checks passed.
- Real 200-light pipeline contract: passed.
- Real 200-light StackEngine contract: passed, default promotion ready.
- Real 200-light guardrails: passed without attaching a resident calibration contract.
- Real 200-light acceptance audit: passed.
- Phase 2 status: green.
- Phase 2 status compare against Gate208: passed, no regression.

## Real Benchmark Evidence

- Native resident calibration artifact masters: 3.
- Native resident calibrated-light ledger rows: 200.
- StackEngine resident calibration contract attached: false.
- StackEngine resident result contract attached: true.
- CUDA resident surfaces in StackEngine contract: 4.
- GLASS resident CUDA elapsed time: 18.804783 s.
- PixInsight/WBPP black-box elapsed time: 1092.541 s.
- Speedup vs WBPP: 58.0991x.
- Active weighted frames: 193.

## Artifacts

- `runs/checkpoints/s2_gate_209_status.md`
- `runs/checkpoints/s2_gate_209_doctor.json`
- `runs/checkpoints/s2_gate_209_real_native_calibration_artifacts.json`
- `runs/checkpoints/s2_gate_209_pipeline_contract.json`
- `runs/checkpoints/s2_gate_209_pipeline_contract.md`
- `runs/checkpoints/s2_gate_209_stack_engine_contract.json`
- `runs/checkpoints/s2_gate_209_stack_engine_contract.md`
- `runs/checkpoints/s2_gate_209_guardrails_summary.json`
- `runs/checkpoints/s2_gate_209_acceptance_contract_bundle.json`
- `runs/checkpoints/s2_gate_209_acceptance_real_native_artifact.json`
- `runs/checkpoints/s2_gate_209_acceptance_real_native_artifact.md`
- `runs/checkpoints/s2_gate_209_phase2_status.json`
- `runs/checkpoints/s2_gate_209_phase2_status.md`
- `runs/checkpoints/s2_gate_209_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_209_phase2_status_compare.md`
- `C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\guardrails\\report.html`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package recommendation: cuda13, with cuda12/cuda11/cpu fallback order.

## Known Limitations

- This gate changes artifact generation and contracts only; it does not change calibration math or image processing kernels.
- Resident calibrated-light rows are ledger entries for frames held in VRAM, not disk-backed calibrated FITS files.
- The real 200-light evidence used a metadata-only contract view of the existing run; no raw images were reprocessed.
- Integration default-promotion still requires the resident result contract artifact.

## Next Step

Proceed to the next Phase 2 gate by making downstream frame accounting/report views prefer the native resident calibration artifact and by reducing dependence on separately generated bridge artifacts.

## Clean-Room Compliance

Compliant. This gate used GLASS source code and GLASS/user-generated artifacts only. It did not read or reuse official PixInsight/WBPP/PJSR source code.
