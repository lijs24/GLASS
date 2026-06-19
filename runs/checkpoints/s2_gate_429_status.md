# S2-Gate 429 Status: Resident GPU Global-Mean Centroid Background

## Gate

S2-Gate 429

## Scope

Return Phase 2 work to substantive runtime goals after the Gate400-413
release/default-promotion/report-chain series. This gate changes the resident
CUDA registration path and validates the effect on the 16-frame synthetic
CPU-vs-resident checkpoint harness.

## Gate400-413 Practical Value

Gate400-413 added useful benchmark-profile and release/default-promotion
handoff guardrails. They make it harder to publish or promote a build while
dropping the `resident_cuda_dq_v1` benchmark/DQ evidence chain.

Their practical value to the core Phase 2 goals is indirect:

- They protect evidence continuity across acceptance, release-decision,
  default-promotion, Windows release-matrix, publish-preflight, Phase2 status,
  and publication-audit artifacts.
- They do not change StackEngine pixel execution, CUDA kernels, star detection,
  registration transforms, warp math, DQ/mask semantics, integration math,
  real 200-light regression behavior, or runtime performance.
- They should be treated as banked guardrails. Do not continue adding
  release/default-promotion/report-contract-only gates unless a missing
  evidence field directly blocks StackEngine default path, DQ/mask contract,
  resident CUDA performance, numerical parity, or real 200-light regression.

## Completed

- Added resident CUDA finite-frame mean reduction support.
- Added `global_mean` centroid background support to resident top-NMS centroid
  refinement.
- Kept `local_median` as an explicit override.
- Made resident triangle registration default to global-mean centroid
  background.
- Added CLI override:
  `--resident-triangle-centroid-background {global_mean,local_median}`.
- Recorded centroid background mode in resident registration artifacts and
  warnings:
  - `triangle_centroid_refine_mode=resident_gpu_global_mean_centroid`
  - `triangle_centroid_refine_background=global_mean`
- Updated resident CUDA tests for the current native batch-warp contract.
- Updated Phase 2 planning docs and algorithm-source notes.

## Commands Run

```powershell
cmd.exe /d /s /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul && "C:\Users\ljs\WORK\astro\gpuwbpp\.venv\Scripts\cmake.exe" --build build\native-cuda-glass --config Release --target _glass_cuda_native'
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_gpu_star_detect.py tests\test_resident_cuda_run.py -k "star_top_nms_candidates_centroid or star_grid_top_nms_candidates or triangle_centroid_refine or triangle_translation_refine"
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli run --plan runs\checkpoints\s2_gate_420_no_pixel_refine_plan.json --out runs\checkpoints\s2_gate_429_global_mean_centroid_refF16_cuda_hardened --backend cuda --tile-size 128 --memory-mode resident --resident-registration similarity_cuda_triangle --reference-frame-id F000016 --local-normalization off --integration-weighting none --integration-rejection winsorized_sigma --resident-winsorized-mode hardened_cpu_parity --resident-output-maps audit
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli resident-warp-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_429_global_mean_centroid_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_429_global_mean_warp_input_audit.json --markdown runs\checkpoints\s2_gate_429_global_mean_warp_input_audit.md
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli resident-rejection-input-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_429_global_mean_centroid_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --out runs\checkpoints\s2_gate_429_global_mean_rejection_input_audit.json --markdown runs\checkpoints\s2_gate_429_global_mean_rejection_input_audit.md --evaluation-region compare_region --max-same-pre-rejection-abs-delta 16
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli resident-rejection-sample-audit --cpu-run runs\checkpoints\s2_gate_414_runtime_validation_cpu --resident-run runs\checkpoints\s2_gate_429_global_mean_centroid_refF16_cuda_hardened --compare-json runs\checkpoints\s2_gate_423_common_footprint_compare.json --rejection-input-audit runs\checkpoints\s2_gate_429_global_mean_rejection_input_audit.json --evaluation-region compare_region --max-pre-rejection-sample-delta 0 --max-same-pre-rejection-abs-delta 0 --max-rejected-sample-delta 0 --out runs\checkpoints\s2_gate_429_global_mean_rejection_sample_attributed_audit.json --markdown runs\checkpoints\s2_gate_429_global_mean_rejection_sample_attributed_audit.md
```

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass_cuda.py src\glass\engine\resident_cuda.py src\glass\cli.py tests\test_resident_cuda_run.py
```

```powershell
.\.venv\Scripts\python.exe -m glass.cli doctor --json runs\checkpoints\s2_gate_429_cuda_doctor.json
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused resident CUDA tests: `5 passed, 56 deselected`.
- Failed full pytest once because two tests still expected an older non-batched
  warp contract.
- Updated those tests to assert the current native batch-warp contract:
  - `triangle_warp_batch_timing_model=native_loop_batched_inverse_one_sync`
  - `resident_registration_application=matrix_bilinear_batch`
  - `resident_registration_application=matrix_lanczos3_batch`
- Focused failing tests after update: `2 passed`.
- Final full pytest: `1007 passed in 38.29s`.
- Ruff: passed.

## CUDA Status

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Driver: 596.21
- Native extension loaded: yes

Doctor artifact:

- `runs/checkpoints/s2_gate_429_cuda_doctor.json`

## Validation Artifacts

- Resident run:
  `runs/checkpoints/s2_gate_429_global_mean_centroid_refF16_cuda_hardened/`
- Warp input audit:
  `runs/checkpoints/s2_gate_429_global_mean_warp_input_audit.json`
- Warp input audit Markdown:
  `runs/checkpoints/s2_gate_429_global_mean_warp_input_audit.md`
- Rejection input audit:
  `runs/checkpoints/s2_gate_429_global_mean_rejection_input_audit.json`
- Rejection input audit Markdown:
  `runs/checkpoints/s2_gate_429_global_mean_rejection_input_audit.md`
- Rejection sample audit:
  `runs/checkpoints/s2_gate_429_global_mean_rejection_sample_attributed_audit.json`
- Rejection sample audit Markdown:
  `runs/checkpoints/s2_gate_429_global_mean_rejection_sample_attributed_audit.md`

## Numerical Result

Comparison against Gate428 guarded-refine artifacts on the same 16-frame
checkpoint harness:

| Metric | Gate428 | Gate429 |
| --- | ---: | ---: |
| Resident matrix translation delta max px | 0.0095319489 | 0.0077076656 |
| Resident matrix warp RMS max | 0.1963685782 | 0.1586616188 |
| Resident output master abs delta sum | 12454.689270 | 6638.656708 |
| Coverage abs delta sum | 1376 | 706 |
| Low rejection abs delta sum | 692 | 356 |
| High rejection abs delta sum | 688 | 350 |
| Compare-region pre-rejection sample delta | 0 | 0 |
| Same-pre-rejection rejected-sample abs delta | 1376 | 706 |

Interpretation:

- The resident global-mean centroid background materially improves the 16-frame
  registration/warp/rejection deltas.
- Exact-input CPU/CUDA hardened winsorized replay still passes in
  `resident-rejection-input-audit`.
- Remaining output-map deltas are still driven by resident registration/warp
  input values and rejection decisions at those values, not by a proven
  standalone rejection-kernel mismatch.

## Performance Note

This gate used the 16-frame synthetic checkpoint harness for numerical
validation, not the real 200-light regression.

The run timing shows the current hot path clearly:

- Total resident run: about `80.420 s`.
- `resident_registration_warp`: about `80.232 s`.
- `triangle_moving_catalog`: about `75.212 s`.
- `triangle_reference_catalog`: about `4.969 s`.
- Hardened winsorized integration itself: about `0.001934 s`.

This makes resident catalog/background/descriptor batching and orchestration
the next runtime optimization target before spending time on the full
200-light regression.

## Known Limitations

- The real 200-light regression was not run in this gate.
- The 16-frame run is small and not a throughput benchmark.
- Resident registration matrix/warp-value parity is still not strict enough
  for rejection-map equality.
- `resident-rejection-sample-audit` still reports attention required at strict
  zero-delta thresholds.
- Local normalization remains disabled in this validation run.

## Next Gate

S2-Gate 430 should target resident catalog batch performance and warp-value
parity:

- reduce per-frame catalog/background/descriptor orchestration cost;
- preserve or improve Gate429 matrix/warp/rejection deltas;
- keep DQ/pre-rejection sample accounting explicit;
- rerun the 16-frame Gate414/Gate423 validation first;
- only then start a real 200-light regression.

## Clean-Room Compliance

Compliant.

- No PixInsight or WBPP/PJSR source was read, copied, summarized, or reworked.
- Only GLASS-generated synthetic checkpoint artifacts and GLASS source/tests
  were used.
- No user input image directory was modified.
- No release or package publication action was performed.
