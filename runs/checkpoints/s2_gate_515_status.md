# S2-Gate 515 Status: Default Shared Resident Master Cache

Gate: S2-Gate 515

Status: passed

Date: 2026-06-23 local

## Objective

Promote the resident master-cache reuse path identified by Gate514 into the
default resident CUDA workflow, so repeated A/B and resume-style runs do not
rebuild identical bias/dark/flat masters in every output directory.

## Completed

- Added `--resident-master-cache-policy {auto,shared,run}` to `glass run` and
  `glass audit`.
- Made `auto` the default policy:
  - explicit `--resident-master-cache-dir` still uses that shared directory;
  - `auto` and `shared` use `RUN_PARENT/resident_master_cache`;
  - `run` preserves the legacy per-run cache under
    `RUN/calib_cache/resident_masters`.
- Recorded master-cache policy evidence in:
  - `run_timing.json`;
  - `resident_artifacts.json` under `resident_io_pipeline`;
  - `resident_master_cache.json` under `policy`.
- Added resident CUDA tests for default auto reuse, explicit run-local policy,
  and the existing explicit shared cache route.
- Updated `docs/phase2_algorithm_hardening.md` and
  `docs/algorithm_sources.md`.

## Code Files

- `src/glass/engine/resident_cuda.py`
- `src/glass/cli.py`
- `tests/test_resident_cuda_run.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`

## Real 200-Light Dataset

- Plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- Manifest: `C:\gpwbpp_runs\final_m38_h_200\manifest.json`
- Frames: 200 light, 20 bias, 20 dark, 20 flat
- WBPP black-box result:
  `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json`
- Run root:
  `C:\glass_runs\phase2_s2_gate515_default_shared_master_cache\runs_20260623_072125`
- Default shared master-cache directory:
  `C:\glass_runs\phase2_s2_gate515_default_shared_master_cache\runs_20260623_072125\resident_master_cache`

## Commands

- `python -m ruff check src\glass\cli.py src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `python -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_auto_master_cache_reuses_output_parent_cache tests/test_resident_cuda_run.py::test_cli_resident_cuda_master_cache_policy_run_keeps_run_local_cache tests/test_resident_cuda_run.py::test_cli_resident_cuda_shared_master_cache_reuses_across_runs`
- Cold default-auto `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps audit --out C:\glass_runs\phase2_s2_gate515_default_shared_master_cache\runs_20260623_072125\cold_auto`
- Warm default-auto `glass run` with the same arguments and
  `--out C:\glass_runs\phase2_s2_gate515_default_shared_master_cache\runs_20260623_072125\warm_auto`
- Cold/warm FITS bitwise comparison script.
- `glass compare` warm master vs WBPP black-box master.
- `glass resident-calibration-contract`
- `glass resident-result-contract --pixel-verify`
- `glass pipeline-contract --pixel-verify`
- `glass stack-engine-contract --expected-integration-engine cuda_resident_stack`
- `glass acceptance-audit --benchmark-contract benchmarks\phase2_m38_h_200_audit_maps_contract.json`
- `python -m pytest -q tests/test_resident_cuda_run.py`
- `python -m pytest -q`
- `glass doctor`

## Test Results

- Focused ruff: passed.
- Focused resident cache pytest: `3 passed in 1.53 s`.
- Resident CUDA run pytest: `80 passed in 8.39 s`.
- Full pytest: `1158 passed in 42.21 s`.
- `glass doctor`: passed.
- Real 200-light cold/warm runs: passed.
- Warm acceptance audit: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real A/B Results

- Cold default-auto internal elapsed: `21.563539599999785 s`.
- Warm default-auto internal elapsed: `16.721956100023817 s`.
- Cold default-auto shell elapsed: `21.945135 s`.
- Warm default-auto shell elapsed: `17.086332 s`.
- Warm/cold speedup:
  - internal: `1.289534518032198x`;
  - shell: `1.284367821016237x`.
- WBPP black-box elapsed: `1092.541 s`.
- Warm speedup vs WBPP:
  - internal: `65.33571751204656x`;
  - shell: `63.942395594326506x`.

## Cache Evidence

- Cold cache summary: `0` hits, `1` miss, scope `shared`.
- Warm cache summary: `1` hit, `0` misses, scope `shared`.
- Policy evidence:
  - requested: `auto`;
  - effective: `shared`;
  - source: `output_parent_default`.
- Master build/load:
  - cold: `4.839396100025624 s`;
  - warm: `0.4271910000243224 s`.
- Resident light read/upload/calibrate wall:
  - cold: `6.9864650000236 s`;
  - warm: `2.55382999998983 s`.

## Numerical Evidence

- Warm master vs cold master:
  - bitwise equal: `true`;
  - RMS: `0`;
  - max absolute difference: `0`;
  - p99 absolute difference: `0`.
- Warm master vs WBPP coverage>=190:
  - shape match: `true`;
  - RMS diff: `0.0017794216505176163`;
  - p99 absolute diff: `0.00042621337808668863`;
  - coverage fraction: `0.960532609259836`;
  - coverage max/median: `193` / `192`.

## Contract Results

- Resident calibration contract: passed.
- Resident result contract: passed with pixel verification.
- Pipeline contract: passed with pixel verification.
- StackEngine contract: passed and default-promotion ready.
- Acceptance audit: passed.

## Artifacts

- Checkpoint summary:
  `runs/checkpoints/s2_gate_515_default_shared_master_cache_summary.json`
- Cold/warm bitwise comparison:
  `C:\glass_runs\phase2_s2_gate515_default_shared_master_cache\runs_20260623_072125\cold_warm_master_compare.json`
- Warm compare report:
  `C:\glass_runs\phase2_s2_gate515_default_shared_master_cache\runs_20260623_072125\warm_auto\s2_gate_515_compare_vs_wbpp.html`
- Warm acceptance audit:
  `C:\glass_runs\phase2_s2_gate515_default_shared_master_cache\runs_20260623_072125\warm_auto\phase2_contract_acceptance_audit_s2_gate_515.json`
- Warm acceptance markdown:
  `C:\glass_runs\phase2_s2_gate515_default_shared_master_cache\runs_20260623_072125\warm_auto\phase2_contract_acceptance_audit_s2_gate_515.md`

## Known Limitations

- This gate improves repeated/default-parent workflows. A first run in a new
  output parent still pays the master build cost.
- Cache fingerprints use GLASS master-cache metadata and file size/mtime tokens
  rather than full calibration-frame checksums, preserving the existing
  no-extra-full-image-read lookup behavior.
- Local normalization remains off for this 200-light benchmark route.
- Resident winsorized sigma remains the documented GLASS fast approximation,
  not a claim of exact PixInsight algorithm identity.

## Next Step

With master-cache reuse now default, return to the remaining warm-path costs:
resident light read/upload/calibration overlap and residual registration/warp
orchestration.

## Clean-Room Compliance

Compliant. This gate used GLASS source, GLASS artifacts, user-staged M38
H-alpha benchmark inputs, and user-generated WBPP black-box timing/reference
outputs. No official PixInsight/WBPP/PJSR implementation source was read,
copied, summarized, or modified. Original image directories remained read-only.
