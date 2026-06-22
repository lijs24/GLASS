# S2-Gate 512 Status: Explicit Resident Warp Chunk Probe

Gate: S2-Gate 512

## Result

Passed.

This gate returns to the Phase 2 resident registration/warp performance target.
It fixes the native batch-warp allocator so an explicit
`--resident-warp-chunk-capacity-frames` value can exceed the old native preferred
chunk of `8`, then validates the change on the real 200-light benchmark.

The real probe is intentionally a negative default-promotion result: larger warp
chunks reduce kernel-launch count and preserve pixels bit-for-bit, but they do
not improve runtime on this dataset/GPU. The default therefore remains native
preferred chunk `8`.

## Completed

- Updated `cpp/src/native_bindings.cpp` so explicit resident matrix-warp chunk
  capacity is honored above `8`.
- Added a CUDA warp regression test proving a 10-frame batch with explicit
  capacity `16` is processed in one chunk instead of being silently truncated to
  `8`.
- Ran real 200-light chunk16/chunk24 probes against the Gate511 default output.
- Saved the probe summary at
  `runs/checkpoints/s2_gate_512_warp_chunk_probe_summary.json`.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands

- `cmake --build build --config Release -j 1` inside the VS BuildTools
  developer environment.
- `python -m pytest -q tests/test_gpu_warp_vs_cpu.py`
- `python -m pytest -q tests/test_gpu_warp_vs_cpu.py tests/test_cli_smoke.py::test_cli_resident_run_passes_explicit_chunk_capacity_from_admission tests/test_resident_cuda_run.py::test_resident_memory_admission_accepts_explicit_chunk_capacity tests/test_resident_cuda_run.py::test_resident_registration_matrix_batch_honors_chunk_capacity`
- `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate510_resident_calibration_contract_ab_real\runs_20260623_063856\shared_master_cache --resident-warp-chunk-capacity-frames 16 --out C:\glass_runs\phase2_s2_gate512_warp_chunk_probe\runs_20260623_065637\chunk16`
- `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate510_resident_calibration_contract_ab_real\runs_20260623_063856\shared_master_cache --resident-warp-chunk-capacity-frames 24 --out C:\glass_runs\phase2_s2_gate512_warp_chunk_probe\runs_20260623_065637\chunk24`
- `python -m ruff check tests/test_gpu_warp_vs_cpu.py`
- `python -m pytest -q`
- `glass doctor`

## Test Result

- Focused CUDA warp tests: `14 passed`.
- Focused Gate512 regression set: `18 passed`.
- Full test suite: `1155 passed in 41.68 s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- CUDA native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Real 200-Light Probe

Probe root:

`C:\glass_runs\phase2_s2_gate512_warp_chunk_probe\runs_20260623_065637`

Baseline:

- Gate511 default run:
  `C:\glass_runs\phase2_s2_gate511_v3_io_prefetch48_default_ab_real\runs_20260623_064914\default_prefetch48`
- Total runtime: `6.5765664000064135 s`.
- Native warp total: `0.4617859 s`.
- Chunk frames: `8`.
- Chunk count: `24`.
- Warp launches: `24`.
- Postprocess launches: `24`.

Chunk16:

- Total runtime: `6.80365089996485 s`.
- Native warp total: `0.4766107 s`.
- Chunk frames: `16`.
- Chunk count: `12`.
- Warp launches: `12`.
- Postprocess launches: `12`.
- Master vs Gate511: bitwise equal, RMS `0.0`, max abs `0.0`.

Chunk24:

- Total runtime: `6.626598200004082 s`.
- Native warp total: `0.4927578 s`.
- Chunk frames: `24`.
- Chunk count: `8`.
- Warp launches: `8`.
- Postprocess launches: `8`.
- Master vs Gate511: bitwise equal, RMS `0.0`, max abs `0.0`.

Decision:

- Do not promote chunk16 or chunk24 to default.
- Keep default resident warp chunk at native preferred `8`.
- Larger chunks are now available as an explicit tuning/probe knob, but this
  benchmark shows that fewer launches do not overcome the larger workspace and
  memory traffic cost.

## Artifacts

- `runs/checkpoints/s2_gate_512_status.md`
- `runs/checkpoints/s2_gate_512_warp_chunk_probe_summary.json`
- `C:\glass_runs\phase2_s2_gate512_warp_chunk_probe\runs_20260623_065637\chunk16`
- `C:\glass_runs\phase2_s2_gate512_warp_chunk_probe\runs_20260623_065637\chunk24`

## Known Limitations

- This gate does not improve the default real 200-light runtime.
- The current resident warp path still writes warped chunks to a workspace and
  scatters them back into the resident frame stack.
- Prior `fused_matrix` probing was faster in the registration component but
  slower end-to-end and not bitwise equal, so it remains unpromoted.

## Next Step

The next substantive gate should target a bitwise-safe warp/integration handoff:
avoid the extra workspace/scatter round trip or batch the warp output directly
into the existing resident integration path while preserving Gate511/Gate512
master pixels.

## Clean-Room Compliance

Passed. This gate uses only GLASS code, GLASS tests, GLASS-generated timing and
output artifacts, and user-provided benchmark data. It does not inspect,
summarize, copy, or rework external proprietary implementation source.
