# S2-Gate 510 Status: Resident Calibration Contract Auto-Bundle

Gate: S2-Gate 510

## Result

Passed.

This gate closes a real Phase 2 StackEngine/DQ contract self-containment gap on
the resident CUDA 200-light path. Resident CUDA runs now emit a top-level
`resident_calibration_contract.json`, record it in `run_state.json`, and
`glass stack-engine-contract --run ...` auto-discovers it without an explicit
`--resident-calibration-contract-json` argument.

## Completed

- Added automatic resident calibration contract generation to
  `src/glass/engine/resident_cuda.py`.
- Added run-default auto-discovery for `resident_calibration_contract.json` in
  `src/glass/report/stack_engine_contract.py`.
- Updated `glass stack-engine-contract` console summary to report calibration
  contract path/source.
- Added focused contract and resident CUDA smoke coverage.
- Updated Phase 2 and algorithm-source documentation.
- Cleaned generated C-drive benchmark outputs before the real run:
  - deleted 40 older generated `C:\glass_runs\phase2_s2_gate480...508...`
    directories;
  - freed `45.69 GiB`;
  - cleanup manifest:
    `C:\glass_runs\cleanup_phase2_gate480_508_20260623_063527.json`.

## Commands

- `python -m ruff check src\glass\engine\resident_cuda.py src\glass\report\stack_engine_contract.py src\glass\cli.py tests\test_stack_engine_contract.py tests\test_resident_cuda_run.py`
- `python -m pytest -q tests\test_stack_engine_contract.py::test_stack_engine_contract_auto_discovers_native_resident_calibration_contract tests\test_stack_engine_contract.py::test_stack_engine_contract_cli_uses_resident_calibration_contract_json`
- `python -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_smoke`
- `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate510_resident_calibration_contract_ab_real\runs_20260623_063856\shared_master_cache --out ...\candidate`
- Same command for `...\repeat`.
- `glass stack-engine-contract --run ...\candidate --scope all --expected-integration-engine cuda_resident_stack --require-default-ready --out ...\candidate_stack_engine_contract.json`
- `glass stack-engine-contract --run ...\repeat --scope all --expected-integration-engine cuda_resident_stack --require-default-ready --out ...\repeat_stack_engine_contract.json`
- `python -m ruff check src tests`
- `python -m pytest -q`

## Test Result

- Focused contract tests: `2 passed`.
- Resident CUDA smoke: `1 passed`.
- Full test suite: `1154 passed in 41.86 s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light A/B

Run root:

`C:\glass_runs\phase2_s2_gate510_resident_calibration_contract_ab_real\runs_20260623_063856`

Results:

- Candidate with fresh shared master cache: `14.848058100033086 s`.
- Repeat with warmed shared master cache: `6.658429500006605 s`.
- WBPP black-box reference time: `1092.541 s`.
- Candidate speedup vs WBPP: `73.58140658121249x`.
- Repeat speedup vs WBPP: `164.08388794969088x`.
- Candidate vs repeat master: bitwise equal, RMS `0.0`, max abs `0.0`.
- Gate510 repeat vs Gate509 repeat master: bitwise equal, RMS `0.0`, max abs
  `0.0`.

Contract audit:

- Candidate and repeat both passed `--require-default-ready`.
- `resident_calibration_contract_attached=true`.
- `resident_calibration_contract_source=run_default`.
- `resident_result_contract_attached=true`.
- `default_path_status=resident_cuda_stack_engine_surface`.
- `default_promotion_ready=true`.
- `phase2_stack_engine_default_gap_count=0`.

WBPP comparison:

- The Gate510 repeat master is bitwise identical to the Gate509 repeat master,
  so the existing Gate509 WBPP image-difference metrics remain valid.
- Inherited WBPP compare source:
  `C:\glass_runs\phase2_s2_gate509_lanczos_unclamped_specialized_ab_real\runs_20260623_062926\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- RMS diff: `0.0017794216505176163`.
- P99 absolute diff: `0.00042621337808668863`.
- Coverage fraction: `0.960532609259836`.
- Gate510 summary:
  `C:\glass_runs\phase2_s2_gate510_resident_calibration_contract_ab_real\runs_20260623_063856\gate510_wbpp_speedup_summary.json`

## Artifacts

- `resident_calibration_contract.json` in candidate and repeat run directories.
- `candidate_stack_engine_contract.json` and `.md`.
- `repeat_stack_engine_contract.json` and `.md`.
- `gate510_master_consistency.json`.
- `gate510_wbpp_speedup_summary.json`.
- `gate510_wbpp_speedup_summary.md`.

## Known Limitations

- Strict native StackEngine default remains false for resident CUDA surfaces:
  the run is contract-ready for the resident CUDA StackEngine surface, not a
  CPU `stack_engine_cpu` native default.
- The latest WBPP image-difference metrics were not recomputed from the original
  WBPP XISF during this gate because the preserved WBPP reference image was not
  present in the current retained run directory. The reuse is justified by
  Gate510 repeat being bitwise identical to the Gate509 repeat master.
- Minimal output-map mode does not write coverage/rejection FITS maps; this is
  expected for the fast benchmark path.
- The next real performance targets remain I/O/upload/calibration overlap and
  more resident registration/warp batching.

## Clean-Room Compliance

Compliant. This gate used GLASS source code, GLASS-generated artifacts, and
user-generated benchmark/WBPP comparison outputs only. No official
PixInsight/WBPP/PJSR source was read or used.

## Next Step

S2-Gate 511 should return to performance work: reduce resident light-loop
I/O/upload/calibration wall time with pinned multi-buffer scheduling and reduce
registration/warp orchestration by batching resident catalog/scoring/warp work
with fewer host/device synchronization points.
