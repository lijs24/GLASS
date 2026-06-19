# S2 Gate 422 Status - Resident Triangle Centroid Refinement

Date: 2026-06-19
Base commit: 4427e29

## Gate Intent

Return from release/report-only work to Phase 2 core execution: resident CUDA registration/warp correctness, DQ/rejection sample accounting, and measured CPU-vs-resident parity on the 16-frame checkpoint subset used by Gates 414/420/421.

Gate 422 is intentionally substantive but not a full parity closure gate. It targets the Gate 421 blocker where resident CUDA triangle registration produced integer-like translations and large edge coverage/rejected-sample drift.

## Gate 400-413 Core Value Summary

- Gate 400-413 mainly hardened release/default-promotion/report contracts, command surfaces, and evidence handoff.
- Their direct value to the core Phase 2 target is limited but useful: artifacts became more auditable, release decisions became reproducible, and regression evidence is easier to compare.
- Their indirect cost is real: they did not materially improve StackEngine default execution, resident CUDA registration, DQ/mask semantics, 200-light regression readiness, or numeric parity.
- Gate 422 therefore stops expanding release/report gates and moves back to the resident CUDA data path.

## Implemented

- Added resident triangle translation refinement from matched resident catalogs.
- Added optional resident catalog centroid refinement using small `ResidentCalibratedStack.download_frame_tile` patches and the CPU star-centroid weighting formula.
- Default enablement is limited to `registration_policy.transform_model == "translation"` for resident `similarity_cuda_triangle`.
- Added per-frame warnings and resident artifact fields for:
  - `triangle_translation_refine_*`
  - `triangle_centroid_refine_*`
- Added unit tests for translation refinement guardrails and centroid refinement from resident tiles.

## Validation Commands

- `.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_resident_refine_catalog_centroids_uses_resident_tiles tests/test_resident_cuda_run.py::test_resident_triangle_translation_refine_uses_catalog_median_translation tests/test_resident_cuda_run.py::test_resident_triangle_translation_refine_rejects_large_correction tests/test_resident_cuda_run.py::test_cli_resident_cuda_triangle_default_skips_pixel_refine tests/test_resident_registration_matrix_compare.py tests/test_resident_rejection_sample_audit.py`
- `.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_422_centroid_refine_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit`
- `.venv\Scripts\python.exe -m glass.cli resident-registration-matrix-compare --baseline-registration runs\checkpoints\s2_gate_414_runtime_validation_cpu\registration_results.json --candidate-registration runs\checkpoints\s2_gate_422_centroid_refine_refF16_cuda_hardened\registration_results.json --out runs\checkpoints\s2_gate_422_centroid_refine_matrix_compare.json --markdown runs\checkpoints\s2_gate_422_centroid_refine_matrix_compare.md --max-translation-delta-px 0.05 --max-matrix-delta-frobenius 0.05`
- `.venv\Scripts\python.exe -m glass.cli resident-rejection-sample-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_422_centroid_refine_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_422_centroid_refine_compare.json --out runs\checkpoints\s2_gate_422_centroid_refine_rejection_sample_audit.json --markdown runs\checkpoints\s2_gate_422_centroid_refine_rejection_sample_audit.md --tile-size 64 --top-tiles 8 --max-rejected-sample-delta 64`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_422_centroid_refine_refF16_cuda_hardened\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_422_centroid_refine_compare.json --diagnostics-dir runs\checkpoints\s2_gate_422_centroid_refine_compare_diagnostics`
- `.venv\Scripts\python.exe -m glass.cli compare --glass runs\checkpoints\s2_gate_422_centroid_refine_refF16_cuda_hardened\integration\resident_master_H.fits --reference runs\checkpoints\s2_gate_414_runtime_validation_cpu\integration\master_H.fits --out runs\checkpoints\s2_gate_422_centroid_refine_compare.html --diagnostics-dir runs\checkpoints\s2_gate_422_centroid_refine_compare_diagnostics`
- `.venv\Scripts\python.exe -m glass.cli resident-parity-summary --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_422_centroid_refine_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_422_centroid_refine_compare.json --out runs\checkpoints\s2_gate_422_centroid_refine_parity_summary.json --markdown runs\checkpoints\s2_gate_422_centroid_refine_parity_summary.md --max-rejected-sample-delta 64`
- `.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_422_cuda_doctor.json`
- `.venv\Scripts\python.exe -m pytest -q`

## Results

- Targeted pytest: 10 passed.
- Full pytest: 998 passed in 37.58s.
- Resident CUDA run completed through integration.
- Matrix compare: passed.
- Translation refinement applied to 15 non-reference frames.
- Centroid refinement processed 16 catalogs and 938 star centroids.
- Maximum translation correction observed: 0.005467 px.
- Rejected sample delta improved from Gate 421 `117` to `15`, passing the `64` threshold.
- Pre-rejection sample delta improved from Gate 421 `10202` to `504`, still not zero.
- Compare RMS is still not within parity threshold:
  - RMS diff: 0.232999
  - relative RMS diff: 0.00106077
  - abs diff p99: 1.04950
- Resident parity summary remains `attention_required`.

## CUDA

CUDA is available. Doctor output reports:

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Recommended package path: cuda

Full report: `runs/checkpoints/s2_gate_422_cuda_doctor.json`

## Artifacts

- `runs/checkpoints/s2_gate_422_centroid_refine_refF16_cuda_hardened/`
- `runs/checkpoints/s2_gate_422_centroid_refine_matrix_compare.json`
- `runs/checkpoints/s2_gate_422_centroid_refine_matrix_compare.md`
- `runs/checkpoints/s2_gate_422_centroid_refine_rejection_sample_audit.json`
- `runs/checkpoints/s2_gate_422_centroid_refine_rejection_sample_audit.md`
- `runs/checkpoints/s2_gate_422_centroid_refine_compare.json`
- `runs/checkpoints/s2_gate_422_centroid_refine_compare.html`
- `runs/checkpoints/s2_gate_422_centroid_refine_compare_diagnostics/`
- `runs/checkpoints/s2_gate_422_centroid_refine_parity_summary.json`
- `runs/checkpoints/s2_gate_422_centroid_refine_parity_summary.md`
- `runs/checkpoints/s2_gate_422_cuda_doctor.json`

## Known Limitations

- Centroid refinement currently uses tiny resident tile downloads plus CPU centroid math. It is an audit/proof step, not the final pure-GPU implementation.
- The resident pipeline is still slower than the CPU checkpoint subset for this small run; this subset is too small to represent the 200-light target workload.
- Coverage/pre-rejection parity is still not closed. Remaining blocker is edge coverage semantics and/or exact CPU-compatible matrix/warp boundary behavior.
- Pixel RMS parity is still attention-required.

## Next Gate

S2 Gate 423 should focus on resident geometric coverage parity:

- Make resident warp/coverage edge semantics match the CPU baseline or explicitly define a common-footprint/crop contract.
- Move the centroid refinement formula into CUDA or a batched resident kernel if it remains required.
- Validate with the same Gate414/420 subset and then scale to the real 200-light regression only after coverage/RMS parity improves.

## Clean-Room

Clean-room constraints remain satisfied. No PixInsight or WBPP/PJSR source was read or used. This gate uses GLASS code, GLASS-generated artifacts, synthetic/checkpoint data, and public CUDA/Numpy-style numerical methods only.
