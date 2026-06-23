# S2-Gate 568 Status: Resident Reference Metadata Closure

## Gate

S2-Gate 568 fixes resident registration reference auditability by writing the
selected reference frame into top-level `registration_results.json`, then uses a
real 200-light no-reference run to evaluate whether first-light fallback is safe
to promote.

## Completed

- Added top-level resident registration reference metadata:
  - `reference_frame_id`
  - `reference_frame_ids`
  - `selected_reference_frame_id`
  - `selected_reference_frame_ids`
  - `reference_selection_source`
  - `reference_selection_sources`
  - `quality_reference_frame_id`
  - `quality_reference_frame_ids`
  - `quality_reference_status`
  - `quality_reference_statuses`
- Single-reference resident runs now expose scalar top-level fields for report,
  compare, and contract consumers.
- Multi-group resident runs keep list fields and avoid inventing a scalar
  reference when multiple references exist.
- Updated the resident CUDA quality-reference handoff test to assert top-level
  metadata closure as well as resident artifact metadata.
- Ran a real 200-light no-reference validation to test the remaining default
  science gap.

## Commands

- `.venv\Scripts\python.exe -m py_compile src\glass\engine\resident_cuda.py tests\test_resident_cuda_run.py`
- `.venv\Scripts\python.exe -m pytest -q tests\test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_uses_quality_reference`
- `.venv\Scripts\python.exe -m glass.cli run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate568_reference_metadata\runs_20260623_185147\auto_reference --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate518_dq_stats_reuse\runs_20260623_094619\resident_master_cache`
- `.venv\Scripts\python.exe -m pytest -q`
- `.venv\Scripts\python.exe -m glass.cli doctor`

## Test Results

- Syntax check: passed.
- Focused quality-reference metadata closure test: `1 passed in 1.15 s`.
- Full pytest: `1218 passed in 45.17 s`.

## Real 200-Light Validation

- Run root:
  `C:\glass_runs\phase2_s2_gate568_reference_metadata\runs_20260623_185147\auto_reference`
- Summary:
  `runs/checkpoints/s2_gate_568_auto_reference_summary.json`
- Shell elapsed: `7.4771534 s`.
- Run timing total: `7.003199999977369 s`.
- WBPP black-box elapsed reference: `1092.541 s`.
- Speedup versus WBPP reference: `156.00596870052698x`.
- The command intentionally omitted `--reference-frame-id` in addition to
  backend/memory/registration/rejection/LN/warp defaults.
- Top-level registration reference: `F000061`.
- Resident artifact reference: `F000061`.
- Reference selection source: `first_light_fallback`.
- Quality reference status: `absent`.
- Reference metadata closure: passed.
- Local-normalization contract: passed.
- Pipeline contract: passed.
- Active/rejected frames: `193 / 7`.
- Output master, weight map, coverage map, low/high rejection maps, and DQ map
  all differ from S2-Gate 567.
- Master diff versus S2-Gate 567 explicit-reference baseline:
  - RMS abs diff: `461.059927596891`
  - mean abs diff: `55.08878680000815`
  - p99 abs diff: `150.2216533660888`
  - max abs diff: `82359.64892196655`

## CUDA

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver: `596.21`.

## Artifacts

- `runs/checkpoints/s2_gate_568_real_run_path.json`
- `runs/checkpoints/s2_gate_568_auto_reference_summary.json`
- Real run `registration_results.json` with top-level reference metadata.
- Real run `resident_artifacts.json` with matching reference metadata.
- Real run `local_norm_contract.json`.
- Real run `pipeline_contract.json`.
- Real run integration master/maps under `integration/`.

## Known Limitations

- This gate fixes metadata closure only. It does not change reference-selection
  priority or registration math.
- The real no-reference run proves first-light fallback is auditable but not safe
  to promote as a scientific default for the 200-light benchmark.
- Current contracts can pass even when the first-light fallback produces a large
  science delta; the next gate should add a quality-reference generation/selection
  path or block first-light fallback for default matrix-registration science runs.

## Next Step

Implement resident default reference admission: either generate/select a quality
reference before resident matrix registration or fail clearly when a default
science run would otherwise use `first_light_fallback`. Validate against the
Gate567 explicit-reference baseline and keep the no-reference path from silently
producing a divergent master.

## Clean-Room Compliance

Compliant. This gate uses GLASS-owned metadata contracts, tests, and user-owned
200-light GLASS artifacts only. It does not inspect external proprietary source
code, copy external algorithms, or modify input image directories.
