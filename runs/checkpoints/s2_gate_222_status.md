# S2-Gate 222 Status

- Gate: S2-Gate 222
- Scope: Default Route Acceptance Evidence
- Status: green
- Date: 2026-06-18
- Commit: pending

## Completed

- Extended benchmark acceptance contract checks so required execution-route
  tokens can pass through either explicit command text or audited runtime
  artifacts.
- `--memory-mode resident` and `--backend cuda` can now be proven by
  `run_timing.json` and `execution_default_resolution` when Gate 221 selected
  the guarded CUDA resident default route.
- `--resident-runtime-preset throughput-v1` can now be proven by runtime default
  metadata or resident I/O pipeline artifacts.
- `--resident-registration similarity_cuda_triangle` can now be proven by
  `resident_artifacts.json` resident registration metadata.
- Scientific parameter tokens remain explicit; `--flat-floor 0.05` still must
  appear in the command unless a future gate adds a dedicated parameter
  artifact.
- Added regression coverage for the default-route acceptance path.
- Documented S2-Gate 222 in `docs/phase2_algorithm_hardening.md`.

## Commands

- `.\\.venv\\Scripts\\glass.exe acceptance-audit --help`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_acceptance_audit.py`
- `.\\.venv\\Scripts\\ruff.exe check src\\glass\\report\\benchmark_contract.py tests\\test_acceptance_audit.py`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest runs\\tmp_s2_gate_222_default_route_acceptance\\manifest.json --glass-run runs\\tmp_s2_gate_222_default_route_acceptance\\glass_run --wbpp-result runs\\tmp_s2_gate_222_default_route_acceptance\\wbpp_result.json --compare-json runs\\tmp_s2_gate_222_default_route_acceptance\\compare.json --benchmark-contract runs\\tmp_s2_gate_222_default_route_acceptance\\contract.json --min-active-frames 190 --min-speedup 2.0 --out runs\\checkpoints\\s2_gate_222_default_route_acceptance_audit.json --markdown runs\\checkpoints\\s2_gate_222_default_route_acceptance_audit.md`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\ruff.exe check .`
- `.\\.venv\\Scripts\\glass.exe doctor --json runs\\checkpoints\\s2_gate_222_doctor.json --allow-cpu-only`
- `.\\.venv\\Scripts\\glass.exe phase2-status --checkpoint-dir runs\\checkpoints --acceptance-audit runs\\checkpoints\\s2_gate_222_default_route_acceptance_audit.json --release-manifest runs\\checkpoints\\s2_gate_194_strict_windows_release_manifest.json --github-release-plan runs\\checkpoints\\s2_gate_219_github_release_plan.json --pipeline-contract runs\\checkpoints\\s2_gate_211_pipeline_contract.json --release-decision runs\\checkpoints\\s2_gate_218_release_promotion_decision.json --out runs\\checkpoints\\s2_gate_222_phase2_status.json --markdown runs\\checkpoints\\s2_gate_222_phase2_status.md --fail-on-not-green`
- `.\\.venv\\Scripts\\glass.exe phase2-status-compare --baseline-status runs\\checkpoints\\s2_gate_221_phase2_status.json --candidate-status runs\\checkpoints\\s2_gate_222_phase2_status.json --out runs\\checkpoints\\s2_gate_222_phase2_status_compare.json --markdown runs\\checkpoints\\s2_gate_222_phase2_status_compare.md --fail-on-regression`

## Test Results

- Acceptance audit pytest: 33 passed in 1.05 s.
- Targeted ruff: all checks passed.
- Full pytest: 513 passed in 28.08 s.
- Full ruff: all checks passed.
- Default-route acceptance audit: passed.
- Phase 2 status: green, latest gate 222.
- Phase 2 status compare: passed, baseline gate 221, candidate gate 222.

## Acceptance Evidence

- Artifact: `runs/checkpoints/s2_gate_222_default_route_acceptance_audit.json`
- Markdown: `runs/checkpoints/s2_gate_222_default_route_acceptance_audit.md`
- The audit command intentionally omitted `--memory-mode resident`,
  `--backend cuda`, `--resident-registration similarity_cuda_triangle`, and
  `--resident-runtime-preset throughput-v1`.
- The required route tokens passed from artifact evidence:
  `run_timing.json`, `execution_default_resolution`, and
  `resident_artifacts.json`.
- The required scientific parameter token `--flat-floor 0.05` passed only
  because it remained explicit in `run_command.txt`.

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Windows package try order: cuda13, cuda12, cuda11, cpu.

## Artifacts

- `runs/checkpoints/s2_gate_222_default_route_acceptance_audit.json`
- `runs/checkpoints/s2_gate_222_default_route_acceptance_audit.md`
- `runs/checkpoints/s2_gate_222_doctor.json`
- `runs/checkpoints/s2_gate_222_phase2_status.json`
- `runs/checkpoints/s2_gate_222_phase2_status.md`
- `runs/checkpoints/s2_gate_222_phase2_status_compare.json`
- `runs/checkpoints/s2_gate_222_phase2_status_compare.md`

## Known Limitations

- This gate changes release/acceptance evidence only; it does not change image
  processing algorithms or resident registration defaults.
- Only execution-route tokens are inferred from artifacts. Scientific parameter
  requirements still need explicit command text until a future gate defines a
  scientific parameter artifact contract.
- The acceptance audit fixture is synthetic contract evidence, not a new
  200-light runtime benchmark.

## Next Step

- S2-Gate 223 should decide whether resident registration receives its own
  guarded default profile, or continue hardening default-route release handoff
  around the existing 200-light benchmark artifacts.

## Clean-Room Compliance

- This gate used only GLASS code, generated contract fixtures, and prior GLASS
  checkpoint artifacts.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or modified.
- Input image directories were not modified.
