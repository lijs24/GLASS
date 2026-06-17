# S2-Gate 214 Status

- Status: green
- Date: 2026-06-18
- Scope: resident registration fast-path acceptance contract

## Completed

- Added a resident registration fast-path collector for `resident_artifacts.json`.
- Added benchmark-contract checks for resident CUDA `similarity_cuda_triangle` fast-path evidence.
- Required descriptor-fit batching, shared reference/moving/output device buffer reuse, batch pixel refinement, native matrix-Lanczos warp batching, asynchronous warp copy mode, positive warp scratch/workspace allocation, and registration component timing rows.
- Added `resident_registration_fastpath` evidence to acceptance-audit JSON and Markdown.
- Updated the M38 H-alpha 200-light benchmark contract with resident registration fast-path requirements.
- Updated Phase 2 hardening docs with S2-Gate 214.
- Added focused pass/fail tests for fast-path contract enforcement.

## Commands Run

- `.\.venv\Scripts\ruff.exe check src\glass\report\benchmark_contract.py src\glass\report\acceptance_audit.py tests\test_acceptance_audit.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_acceptance_audit.py`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest "C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident\manifest.json" --glass-run "C:\glass_runs\phase2_s2_gate_209_native_artifact\contract_view" --wbpp-result "C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json" --compare-json "C:\glass_runs\phase2_s2_gate_181_default_runtime\default_vs_reference.json" --benchmark-contract benchmarks\phase2_m38_h_200_contract.json --contract-bundle "C:\glass_runs\phase2_s2_gate_211_native_result_contract\guardrails\acceptance_contract_bundle.json" --out runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --markdown runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.md --min-active-frames 190`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_214_doctor.json`
- `.\.venv\Scripts\glass.exe phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --release-manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_213_github_release_plan.json --out runs\checkpoints\s2_gate_214_phase2_status.json --markdown runs\checkpoints\s2_gate_214_phase2_status.md --fail-on-not-green`
- `.\.venv\Scripts\glass.exe phase2-status-compare --baseline-status runs\checkpoints\s2_gate_213_phase2_status.json --candidate-status runs\checkpoints\s2_gate_214_phase2_status.json --out runs\checkpoints\s2_gate_214_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_214_phase2_status_compare.md --fail-on-regression`
- `.\.venv\Scripts\glass.exe windows-github-release-plan --manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --tag v0.1.0-phase2-gate214 --title "GLASS Phase 2 Gate 214 Windows packages" --out runs\checkpoints\s2_gate_214_github_release_plan.json --markdown runs\checkpoints\s2_gate_214_github_release_plan.md --notes runs\checkpoints\s2_gate_214_release_notes.md --script runs\checkpoints\s2_gate_214_publish_release.ps1 --phase2-status runs\checkpoints\s2_gate_214_phase2_status.json --phase2-status-compare runs\checkpoints\s2_gate_214_phase2_status_compare.json --require-same-source-stamp --fail-on-failure`

## Test Results

- Focused pytest: 32 passed in 0.97 s.
- Full pytest: 502 passed in 26.92 s.
- Ruff: all checks passed.
- Real acceptance audit: passed, speedup vs WBPP 58.099101701945926x.
- Resident registration fast-path contract checks: 24 passed.
- Phase 2 status: green, latest gate 214.
- Phase 2 status compare: passed, baseline gate 213, candidate gate 214.
- Windows GitHub release plan: release_plan_ready, publication_ready true.

## Real Fast-Path Evidence

- Resident registration mode: `similarity_cuda_triangle`.
- Descriptor fit batch: true.
- Descriptor fit batch mode: `native_batch_shared_reference_device`.
- Descriptor reference/moving/output device reuse: true.
- Pixel refine batch: true.
- Pixel refine metric mode: `flattened_frame_candidate_grid`.
- Triangle warp batch: true.
- Triangle warp batch mode: `native_matrix_lanczos3_frames`.
- Triangle warp batch frame count: 188.
- Warp copy mode: `default_stream_async_device_to_device`.
- Warp scratch bytes: 493209636.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Artifacts

- `runs/checkpoints/s2_gate_214_acceptance_real_fastpath_contract.json`
- `runs/checkpoints/s2_gate_214_acceptance_real_fastpath_contract.md`
- `runs/checkpoints/s2_gate_214_doctor.json`
- `runs/checkpoints/s2_gate_214_phase2_status.json`
- `runs/checkpoints/s2_gate_214_phase2_status.md`
- `runs/checkpoints/s2_gate_214_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_214_phase2_status_compare.md`
- `runs/checkpoints/s2_gate_214_github_release_plan.json`
- `runs/checkpoints/s2_gate_214_github_release_plan.md`
- `runs/checkpoints/s2_gate_214_release_notes.md`
- `runs/checkpoints/s2_gate_214_publish_release.ps1`

## Known Limitations

- This gate is contract/reporting only. It does not change image math, GPU kernels, or runtime scheduling.
- The real-data evidence reuses the preserved resident CUDA run from `C:\glass_runs\phase2_s2_gate_209_native_artifact\contract_view`.

## Next Step

- Continue Phase 2 by promoting this fast-path evidence into broader release/phase2 status summaries or by starting the next resident registration/warp runtime optimization gate.

## Clean-Room Compliance

- Compliant. This gate uses GLASS-generated artifacts and user-generated black-box comparison metadata only; it does not read or derive implementation details from proprietary PixInsight/WBPP/PJSR source code.
