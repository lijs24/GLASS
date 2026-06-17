# S2-Gate 221 Status

- Gate: S2-Gate 221
- Scope: Guarded Resident CUDA Default Route
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Promoted `glass run` and the run portion of `glass audit` to a guarded
  resident CUDA default route.
- `--memory-mode` now defaults to `resident`.
- `glass run` now defaults `--until-stage` to `integration`, matching full
  pipeline execution.
- With `--backend auto`, CUDA availability promotes the effective route to
  `backend=cuda`, `memory_mode=resident`.
- CPU-only, explicit `--backend cpu`, partial `--until-stage`, explicit
  tile-mode registration, or resident-unsupported integration policies fall
  back to tile mode unless the user explicitly requested `--memory-mode
  resident`.
- Explicit `--memory-mode resident` remains strict and fails clearly if CUDA is
  unavailable or a non-CUDA backend is selected.
- `run_timing.json` now records requested/effective backend and memory-mode
  resolution in `execution_default_resolution`.
- Documented S2-Gate 221 in `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\cli.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_pipeline_fixture.py tests\\test_pipeline_contract.py tests\\test_stack_engine_contract.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_default_promotion_manifest.py tests\\test_release_promotion_decision.py tests\\test_phase2_status.py`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe synthetic --out runs\\tmp_s2_gate_221_default_smoke\\data --frames 3 --width 32 --height 32 --known-shift`
- `.\\.venv\\Scripts\\glass.exe scan --root runs\\tmp_s2_gate_221_default_smoke\\data --out runs\\tmp_s2_gate_221_default_smoke\\manifest.json`
- `.\\.venv\\Scripts\\glass.exe plan --manifest runs\\tmp_s2_gate_221_default_smoke\\manifest.json --out runs\\tmp_s2_gate_221_default_smoke\\processing_plan.json`
- `.\\.venv\\Scripts\\glass.exe run --plan runs\\tmp_s2_gate_221_default_smoke\\processing_plan.json --out runs\\tmp_s2_gate_221_default_smoke\\default_run --local-normalization off --integration-weighting none --integration-rejection none --resident-registration off`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_221_doctor.json --allow-cpu-only`
- `.\\.venv\\Scripts\\glass.exe default-promotion-manifest --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --phase2-status runs\\checkpoints\\s2_gate_220_phase2_status.json --doctor-json runs\\checkpoints\\s2_gate_221_doctor.json --require-doctor --min-runtime-runs 3 --out runs\\checkpoints\\s2_gate_221_default_promotion_manifest.json --markdown runs\\checkpoints\\s2_gate_221_default_promotion_manifest.md --fail-on-not-ready`
- `.\\.venv\\Scripts\\glass.exe run --help`
- `.\\.venv\\Scripts\\glass.exe audit --help`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_214_acceptance_real_fastpath_contract.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_219_github_release_plan.json --pipeline-contract runs\\checkpoints\\s2_gate_211_pipeline_contract.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --out runs\\checkpoints\\s2_gate_221_phase2_status.json --markdown runs\\checkpoints\\s2_gate_221_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_220_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_221_phase2_status.json --out runs\\checkpoints\\s2_gate_221_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_221_phase2_status_compare.md --fail-on-regression`

## Test Results

- CLI smoke pytest: 21 passed in 2.40 s.
- Pipeline/contract pytest: 39 passed in 8.26 s.
- Promotion/status pytest: 14 passed in 0.40 s.
- Full ruff: all checks passed.
- Full pytest: 512 passed in 28.08 s.

## Default Route Smoke

- Artifact: `runs/checkpoints/s2_gate_221_default_route_smoke.json`
- Requested backend: `auto`.
- Requested memory mode: `resident`.
- Effective backend: `cuda`.
- Effective memory mode: `resident`.
- Resolution reason: `resident_cuda_default`.
- Completed resident stages: `master_calibration`, `resident_light_calibration`,
  `resident_integration`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Artifacts

- `runs/checkpoints/s2_gate_221_default_route_smoke.json`
- `runs/checkpoints/s2_gate_221_doctor.json`
- `runs/checkpoints/s2_gate_221_default_promotion_manifest.json`
- `runs/checkpoints/s2_gate_221_default_promotion_manifest.md`
- `runs/checkpoints/s2_gate_221_phase2_status.json`
- `runs/checkpoints/s2_gate_221_phase2_status.md`
- `runs/checkpoints/s2_gate_221_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_221_phase2_status_compare.md`

## Known Limitations

- This gate changes execution routing defaults only; it does not change
  registration science defaults.
- Resident CUDA still supports only the integration end stage; partial stages
  use the tile route unless resident mode is explicitly requested, in which case
  GLASS fails clearly.
- The default resident smoke used a tiny synthetic dataset. The 200-light
  performance proof remains the controlled S2-Gate 218 repeat evidence.

## Next Step

- S2-Gate 222 should update release handoff/benchmark contract wording around
  the new default route and decide whether resident registration should receive
  its own guarded default profile.

## Clean-Room Compliance

- This gate used only GLASS code, generated synthetic data, and prior GLASS
  checkpoint artifacts.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Input image directories were not modified.
