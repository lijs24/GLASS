# S2-Gate 218 Status

- Gate: S2-Gate 218
- Scope: Controlled Runtime Repeat Default-Promotion Evidence
- Status: green
- Date: 2026-06-18

## Completed

- Generated a real 3-repeat runtime plan from the accepted 200-light resident
  CUDA run command.
- Ran a GPU-ready preflight and executed all three repeats on the same M38
  H-alpha 200-light configuration.
- Generated checkpoint-local resident runtime compare artifacts.
- Fed the runtime compare artifact into `glass release-promotion-decision`
  together with the real acceptance audit, StackEngine contract, and pipeline
  DQ contract.
- Promoted the release decision from release-candidate-ready to
  default-change-ready with repeated timing evidence.
- Updated Phase 2 hardening documentation.

## Commands

- `.\.venv\Scripts\glass.exe resident-runtime-repeat-plan --base-run-command "C:\glass_runs\phase2_s2_gate_181_default_runtime\default_resident\run_command.txt" --root "C:\glass_runs\phase2_s2_gate_218_runtime_repeat" --label gate218_default --repeats 3 --cache-state warm --baseline-repeat 2 --out runs\checkpoints\s2_gate_218_runtime_repeat_plan.json --markdown runs\checkpoints\s2_gate_218_runtime_repeat_plan.md`
- `.\.venv\Scripts\glass.exe resident-runtime-repeat-preflight --plan runs\checkpoints\s2_gate_218_runtime_repeat_plan.json --out runs\checkpoints\s2_gate_218_runtime_repeat_preflight.json --min-free-mib 12000 --max-busy-utilization 95`
- `.\.venv\Scripts\glass.exe resident-runtime-repeat-execute --plan runs\checkpoints\s2_gate_218_runtime_repeat_plan.json --out runs\checkpoints\s2_gate_218_runtime_repeat_execution.json --glass-executable .\.venv\Scripts\glass.exe --cwd C:\Users\ljs\WORK\astro\gpuwbpp --require-preflight-ready --min-free-mib 12000 --max-busy-utilization 95`
- `.\.venv\Scripts\glass.exe resident-runtime-compare --run gate218_default_repeat01=C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runs\gate218_default_repeat01 --run gate218_default_repeat02=C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runs\gate218_default_repeat02 --run gate218_default_repeat03=C:\glass_runs\phase2_s2_gate_218_runtime_repeat\runs\gate218_default_repeat03 --baseline-label gate218_default_repeat02 --out runs\checkpoints\s2_gate_218_runtime_compare.json --markdown runs\checkpoints\s2_gate_218_runtime_compare.md`
- `.\.venv\Scripts\glass.exe release-promotion-decision --acceptance-audit runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --stack-engine-contract runs\checkpoints\s2_gate_211_stack_engine_contract.json --pipeline-contract runs\checkpoints\s2_gate_211_pipeline_contract.json --runtime-compare runs\checkpoints\s2_gate_218_runtime_compare.json --repeat-preflight runs\checkpoints\s2_gate_218_runtime_repeat_preflight.json --out runs\checkpoints\s2_gate_218_release_promotion_decision.json --markdown runs\checkpoints\s2_gate_218_release_promotion_decision.md --min-runtime-runs 3 --max-elapsed-ratio-vs-best 1.25 --min-speedup 2.0 --fail-on-not-ready`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_218_doctor.json`
- `.\.venv\Scripts\glass.exe phase2-status --checkpoint-dir runs\checkpoints --acceptance-audit runs\checkpoints\s2_gate_214_acceptance_real_fastpath_contract.json --pipeline-contract runs\checkpoints\s2_gate_211_pipeline_contract.json --release-manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\checkpoints\s2_gate_217_github_release_plan.json --out runs\checkpoints\s2_gate_218_phase2_status.json --markdown runs\checkpoints\s2_gate_218_phase2_status.md --fail-on-not-green`
- `.\.venv\Scripts\glass.exe phase2-status-compare --baseline-status runs\checkpoints\s2_gate_217_phase2_status.json --candidate-status runs\checkpoints\s2_gate_218_phase2_status.json --out runs\checkpoints\s2_gate_218_phase2_status_compare.json --markdown runs\checkpoints\s2_gate_218_phase2_status_compare.md --fail-on-regression`
- `.\.venv\Scripts\glass.exe windows-github-release-plan --manifest runs\checkpoints\s2_gate_194_strict_windows_release_manifest.json --tag v0.1.0-phase2-gate218 --title "GLASS Phase 2 Gate 218 Windows packages" --out runs\checkpoints\s2_gate_218_github_release_plan.json --markdown runs\checkpoints\s2_gate_218_github_release_plan.md --notes runs\checkpoints\s2_gate_218_release_notes.md --script runs\checkpoints\s2_gate_218_publish_release.ps1 --phase2-status runs\checkpoints\s2_gate_218_phase2_status.json --phase2-status-compare runs\checkpoints\s2_gate_218_phase2_status_compare.json --require-same-source-stamp --fail-on-failure`

## Test Results

- Full ruff: passed.
- Full pytest: 503 passed in 27.44s.
- Doctor: passed with CUDA native extension available.
- Runtime repeat preflight: ready_to_execute true.
- Runtime repeat execution: completed, 3/3 runs completed, compare completed.
- Release promotion decision: default_change_ready, recommendation promote_default_candidate.
- Phase 2 status: green, latest gate 218.
- Phase 2 status compare: passed, baseline gate 217, candidate gate 218.
- Windows GitHub release plan: release_plan_ready, publication_ready true, 4 assets.

## Runtime Evidence

- Repeat 1 elapsed: 23.807757599999604 s.
- Repeat 2 elapsed: 22.598500299995067 s.
- Repeat 3 elapsed: 22.745533199995407 s.
- Best repeat: gate218_default_repeat02.
- Slowest/best elapsed ratio: 1.053510511049479.
- Required max slowest/best ratio: 1.25.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Native extension loaded: yes.

## Real Benchmark / Contract Evidence

- Real acceptance evidence source: `runs/checkpoints/s2_gate_214_acceptance_real_fastpath_contract.json`.
- Real stack contract source: `runs/checkpoints/s2_gate_211_stack_engine_contract.json`.
- Real pipeline contract source: `runs/checkpoints/s2_gate_211_pipeline_contract.json`.
- Repeat run root: `C:\glass_runs\phase2_s2_gate_218_runtime_repeat`.
- Input image directories remained read-only.

## Artifacts

- `runs/checkpoints/s2_gate_218_runtime_repeat_plan.json`
- `runs/checkpoints/s2_gate_218_runtime_repeat_plan.md`
- `runs/checkpoints/s2_gate_218_runtime_repeat_preflight.json`
- `runs/checkpoints/s2_gate_218_runtime_repeat_execution.json`
- `runs/checkpoints/s2_gate_218_runtime_compare.json`
- `runs/checkpoints/s2_gate_218_runtime_compare.md`
- `runs/checkpoints/s2_gate_218_release_promotion_decision.json`
- `runs/checkpoints/s2_gate_218_release_promotion_decision.md`
- `runs/checkpoints/s2_gate_218_doctor.json`
- `runs/checkpoints/s2_gate_218_phase2_status.json`
- `runs/checkpoints/s2_gate_218_phase2_status.md`
- `runs/checkpoints/s2_gate_218_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_218_phase2_status_compare.md`
- `runs/checkpoints/s2_gate_218_github_release_plan.json`
- `runs/checkpoints/s2_gate_218_github_release_plan.md`
- `runs/checkpoints/s2_gate_218_release_notes.md`
- `runs/checkpoints/s2_gate_218_publish_release.ps1`

## Known Limitations

- This gate validates repeated runtime and promotion readiness; it does not
  change image math, CUDA kernels, or pipeline defaults by itself.
- Runtime evidence is machine-specific and reflects this workstation's GPU,
  driver, storage, and cache state.
- The next gate should wire this default-change-ready decision into the
  release/default promotion path rather than merely recording it.

## Next Step

- Use the default-change-ready release decision to gate any StackEngine/default
  promotion switch and to expose the repeat evidence in Phase 2/release handoff.

## Clean-Room

- Compliant. No PixInsight/WBPP/PJSR source was read, copied, summarized, or
  reworked.
