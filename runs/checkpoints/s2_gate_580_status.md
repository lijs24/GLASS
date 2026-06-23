# S2-Gate 580 Status: Resident in-VRAM Warp-Quality Benchmark Gate

## Gate

S2-Gate 580

## Completed

- Added a resident in-VRAM surface to `warp-quality-contract` for the real
  resident CUDA default route that does not materialize per-frame registered
  FITS caches.
- `warp-quality-contract` now accepts `registration_results.json` files using
  either `registration_results` or `results`.
- Resident warp-quality checks now validate:
  - resident warp surface presence;
  - active resident output count;
  - skipped-frame reasons;
  - active/masked frame-mask closure;
  - geometric warp coverage frame-count closure;
  - coverage/DQ output map availability when required;
  - geometric valid-fraction threshold;
  - skipped-frame threshold;
  - accepted registration frames against active resident warp frames.
- Resident in-VRAM pixel verification is deliberately not faked. If callers
  request per-frame `--pixel-verify` on this resident surface, the contract
  fails with `resident_warp_pixel_verification_not_supported`; pixel-level
  integration verification remains covered by the pipeline contract.
- `acceptance-audit` now passes warp-quality contract evidence into benchmark
  contract checks and treats benchmark-required warp-quality evidence as
  required even without `--require-warp-quality-contract`.
- `benchmarks/phase2_m38_h_200_ln_on_default_contract.json` now requires a
  passing `resident_in_vram` warp-quality contract with at least `190` resident
  outputs.
- Updated docs:
  - `docs/phase2_algorithm_hardening.md`;
  - `docs/algorithm_sources.md`.

## Commands

- `.venv\Scripts\python.exe -m py_compile src\glass\report\warp_quality.py src\glass\report\benchmark_contract.py src\glass\report\acceptance_audit.py tests\test_acceptance_audit.py tests\test_warp_quality_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_warp_quality_contract.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py -k "warp_quality or contract_bundle"`
- `.venv\Scripts\python.exe -m pytest -q tests\test_warp_quality_contract.py tests\test_acceptance_audit.py`
- `.venv\Scripts\glass.exe warp-quality-contract --run C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default --out C:\glass_runs\phase2_s2_gate580_resident_warp_quality\warp_quality_contract.json --markdown C:\glass_runs\phase2_s2_gate580_resident_warp_quality\warp_quality_contract.md --min-valid-fraction 0.80 --max-skipped-frames 7 --require-all-registered --require-artifacts`
- `.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\manifest.json --glass-run C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\compare_vs_wbpp_fastintegration_scaled_coverage190.json --out C:\glass_runs\phase2_s2_gate580_resident_warp_quality\acceptance_audit_gate580.json --markdown C:\glass_runs\phase2_s2_gate580_resident_warp_quality\acceptance_audit_gate580.md --benchmark-contract benchmarks\phase2_m38_h_200_ln_on_default_contract.json --pipeline-contract-json C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\pipeline_contract_pixel_verify.json --stack-engine-contract-json C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default\stack_engine_contract.json --warp-quality-contract-json C:\glass_runs\phase2_s2_gate580_resident_warp_quality\warp_quality_contract.json`
- `.venv\Scripts\glass.exe doctor --json C:\glass_runs\phase2_s2_gate580_resident_warp_quality\doctor.json`
- `.venv\Scripts\python.exe -m pytest -q`
- `git diff --check`

Note: an initial `glass doctor --out ...` attempt failed because the command
uses `--json`, not `--out`; the corrected `--json` command passed.

## Test Results

- Focused warp-quality contract tests: `6 passed in 0.18s`.
- Focused acceptance warp-quality/contract-bundle tests: `11 passed, 38 deselected in 0.37s`.
- Combined warp-quality and acceptance-audit tests: `55 passed in 1.47s`.
- Post-tightening focused tests: `17 passed, 38 deselected in 0.51s`.
- Full test suite: `1246 passed in 53.41s`.
- `git diff --check`: passed.

## Real 200-Light Validation

- Source run:
  `C:\glass_runs\phase2_s2_gate579_current_default_contract\current_head_default`
- Warp-quality contract:
  `C:\glass_runs\phase2_s2_gate580_resident_warp_quality\warp_quality_contract.json`
- Warp-quality markdown:
  `C:\glass_runs\phase2_s2_gate580_resident_warp_quality\warp_quality_contract.md`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate580_resident_warp_quality\acceptance_audit_gate580.json`
- Acceptance markdown:
  `C:\glass_runs\phase2_s2_gate580_resident_warp_quality\acceptance_audit_gate580.md`
- Doctor report:
  `C:\glass_runs\phase2_s2_gate580_resident_warp_quality\doctor.json`

## Key Results

- Warp-quality contract: `passed`.
- Contract surface: `resident_in_vram`.
- Active/masked resident frames: `193 / 7`.
- Artifact-ready active frames: `193`.
- Geometric warp coverage frames: `193`.
- Geometric valid fraction: `0.9721536969272293`.
- Accepted registration closure: `193 / 193`, `0` missing, `0` extra.
- Warp-quality failed checks: `0`.
- Acceptance audit: `passed`.
- Acceptance checks: no failed checks.
- Speedup vs WBPP black-box reference: `141.03664797477745x`.
- Frame counts: `200 light / 20 bias / 20 dark / 20 flat`.
- Compare shape match: `true`.
- RMS diff vs WBPP: `0.005340835487175878`.
- p99 abs diff vs WBPP: `0.002133606873685496`.
- Coverage190 fraction after border crop: `0.905523489118409`.
- Benchmark-required warp checks:
  - `contract_warp_quality_contract_present`: passed;
  - `contract_warp_quality_contract_surface`: passed;
  - `contract_warp_quality_contract_passed`: passed;
  - `contract_warp_quality_contract_min_check_count`: passed (`9 >= 7`);
  - `contract_warp_quality_contract_min_output_count`: passed (`193 >= 190`);
  - `contract_warp_quality_contract_no_failed_checks`: passed.

## CUDA

- CUDA available: yes.
- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- GPU: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.
- Package recommendation: `cuda`.
- This gate did not change CUDA kernels or image math.

## Known Limitations

- This gate does not improve resident registration/warp runtime. It hardens the
  engineering contract around the resident warp surface so future performance
  work has a guardrail.
- Resident `warp-quality-contract --pixel-verify` intentionally fails because
  the resident path does not write per-frame registered/coverage/DQ caches.
  Use `pipeline-contract --pixel-verify` for pixel-level integration closure.
- The contract validates output map existence and geometric coverage closure;
  it does not replay every per-frame warp tile.
- The older `benchmarks/phase2_m38_h_200_contract.json` was not changed in this
  gate; the active LN-on default benchmark is now tightened.

## Next Step

Proceed to a substantive resident registration/warp execution gate: reduce
per-frame Python orchestration and host/device round trips while preserving the
new Gate580 warp-quality contract, the Gate579 DQ contract, and the real
200-light WBPP comparison.

## Clean-Room Compliance

- Used GLASS source code, GLASS-generated resident artifacts, user-owned
  200-light GLASS outputs, and user-generated WBPP black-box timing/reference
  outputs.
- Did not read, copy, summarize, or rework external proprietary source code.
- Did not modify input image directories.
- Did not change public claims beyond measured GLASS artifacts.
