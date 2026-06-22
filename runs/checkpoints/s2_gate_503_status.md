# S2-Gate 503 Status: Batched Triangle Descriptor Generation

## Gate

S2-Gate 503

## Completed Content

- Continued the Phase 2 resident registration/warp performance path after Gate502.
- Added CUDA batch generation for triangle asterism descriptors:
  - `triangle_asterism_descriptor_batch_kernel`
  - `glass_triangle_asterism_descriptors_batch_f32_launch`
  - native pybind API `triangle_asterism_descriptors_batch_f32`
  - Python wrapper/fallback `glass_cuda.triangle_asterism_descriptors_batch_f32`
- Routed resident `similarity_cuda_triangle` moving-catalog descriptor generation through the batch API when available.
- Preserved old per-catalog descriptor generation as fallback.
- Added resident artifact fields:
  - `triangle_descriptor_generation_batch`
  - `triangle_descriptor_generation_batch_mode`
  - `triangle_descriptor_generation_batch_call_count`
  - `triangle_descriptor_generation_batch_size`
  - `triangle_descriptor_generation_batch_timing_model`
  - `triangle_descriptor_generation_batch_upload_s`
  - `triangle_descriptor_generation_batch_kernel_sync_s`
  - `triangle_descriptor_generation_batch_output_download_s`
- Rebuilt `_glass_cuda_native` locally with CUDA 13.2 and Visual Studio Build Tools.

## Files Changed

- `cpp/cuda/registration_kernels.cu`
- `cpp/src/native_bindings.cpp`
- `src/glass_cuda.py`
- `src/glass/engine/resident_cuda.py`
- `tests/test_gpu_registration_search.py`
- `docs/phase2_algorithm_hardening.md`
- `docs/algorithm_sources.md`

## Real 200-Light Validation

Run root:

`C:\glass_runs\phase2_s2_gate503_descriptor_batch_ab_real\runs_20260623_052608`

Baseline:

`C:\glass_runs\phase2_s2_gate502_warp_chunk_capacity_ab_real\runs_20260623_051320\default_auto8`

Common run settings:

- plan: `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
- master cache: `C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache`
- backend: `cuda`
- memory mode: `resident`
- resident registration: `similarity_cuda_triangle`
- reference frame: `LIGHT_H_0136`
- warp interpolation: `lanczos3`
- output maps: `minimal`
- rejection: `winsorized_sigma`
- weighting: `none`
- local normalization: `off`
- flat floor: `0.05`
- runtime preset: default `throughput-v3-io`

Timing:

| Variant | Total | Registration component | Moving descriptors | Output write |
| --- | ---: | ---: | ---: | ---: |
| Gate502 default | `7.12994339998113 s` | `2.0864001998257167 s` | `0.1319461001548916 s` | `0.5232929000048898 s` |
| Gate503 default | `7.1556646000244655 s` | `2.0023035002699507 s` | `0.05534540000371635 s` | `0.612973100040108 s` |
| Gate503 repeat | `7.309961199993268 s` | `2.0049072001437387 s` | `0.05633970000781119 s` | `0.7726493999944068 s` |

Descriptor-generation artifact evidence:

- `triangle_descriptor_generation_batch`: `true`
- `triangle_descriptor_generation_batch_mode`: `native_batch_padded_catalog_one_sync`
- `triangle_descriptor_generation_batch_timing_model`: `padded_catalog_batch_one_kernel_one_sync`
- `triangle_descriptor_generation_batch_call_count`: `1`
- `triangle_descriptor_generation_batch_size`: `198`
- `triangle_descriptor_generation_batch_kernel_sync_s`: about `0.000073 s`

## Numerical Results

Gate503 default versus Gate502 default:

- bitwise equal: `true`
- RMS absolute difference: `0.0`
- p99 absolute difference: `0.0`
- max absolute difference: `0.0`

Gate503 repeat versus Gate502 default:

- bitwise equal: `true`
- RMS absolute difference: `0.0`
- p99 absolute difference: `0.0`
- max absolute difference: `0.0`

WBPP black-box timing retained for speed context:

- WBPP elapsed: `1092.541 s`
- Gate503 default speedup by GLASS run timing: about `152.684x`
- Gate503 repeat speedup by GLASS run timing: about `149.459x`

## Interpretation

- This gate gives a stable resident registration component win:
  - moving descriptor generation reduced by about `0.076 s`
  - registration component reduced by about `0.081-0.084 s`
- End-to-end timing did not improve in the recorded runs because final output write varied by about `0.09-0.25 s` versus Gate502.
- The change is still useful because it removes one more per-frame native call/sync/download loop from the resident registration path.
- The next larger target remains native warp kernel/sync and output-write variability.

## Commands Run

- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && .venv\Scripts\cmake.exe -S . -B build -G Ninja -DGLASS_BUILD_PYTHON_CUDA=ON -DGLASS_CUDA_RUNTIME_LIBRARY=Shared -DPython3_EXECUTABLE=%CD%\.venv\Scripts\python.exe -Dpybind11_DIR=%CD%\.venv\Lib\site-packages\pybind11\share\cmake\pybind11'`
- `cmd.exe /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" && .venv\Scripts\cmake.exe --build build --target _glass_cuda_native --config Release -j 8'`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_gpu_registration_search.py::test_gpu_triangle_asterism_descriptor_batch_matches_single_catalogs tests/test_gpu_registration_search.py::test_gpu_triangle_descriptor_similarity_batch_matches_single_fits`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair tests/test_gpu_registration_search.py`
- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate503_descriptor_batch_ab_real\runs_20260623_052608\default_descriptor_batch --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache`
- the same command to `default_descriptor_batch_repeat`
- `.\.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Focused descriptor tests: `2 passed in 0.49s`
- Focused resident/registration tests: `35 passed in 0.87s`
- Full test suite: `1149 passed in 41.74s`

## CUDA Status

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`
- Compute capability: `12.0`
- Reported memory: `97886 MiB`
- Native module rebuilt with CUDA Toolkit `13.2.78`.

## Known Limits

- The batch descriptor API still downloads raw descriptors to host for the existing deterministic sort/dedup contract.
- The resident artifact currently records the first batch timing payload; future work can expose fuller per-batch aggregate timing if multiple thresholds are used.
- This gate improves the registration component but is not claimed as an end-to-end speed improvement because output-write timing dominated the recorded total delta.

## Next Step

Continue resident registration/warp optimization by reducing native warp kernel/sync cost and stabilizing output/write timing. Descriptor generation is now a smaller fraction of the registration component.

## Clean-Room Compliance

Compliant. This gate implements GLASS-owned CUDA batching over existing GLASS triangle descriptor logic and validates against GLASS single-catalog outputs plus user-staged 200-light data. It does not inspect external implementation source, copy proprietary behavior, modify input image directories, or change scientific formulas.
