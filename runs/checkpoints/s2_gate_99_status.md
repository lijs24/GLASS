# S2-Gate 99 Status: Resident Registration Component Sweep Reporting

## Gate

S2-Gate 99: Resident Registration Component Sweep Reporting

## Completed Content

- Promoted resident registration/warp component timings from
  `resident_artifacts.json` into `resident_prefetch_sweep_summary.json`.
- Added Markdown sweep columns for:
  - total resident registration/warp wall time
  - triangle moving catalog time
  - triangle pixel refinement time
  - triangle warp time
- Added JSON sweep fields for:
  - `registration_component_accounted_s`
  - `registration_triangle_moving_catalog_s`
  - `registration_triangle_descriptor_fit_s`
  - `registration_triangle_moving_descriptors_s`
  - `registration_triangle_pixel_refine_s`
  - `registration_triangle_warp_s`
  - `registration_triangle_warp_native_batch_s`
- Kept older runs reportable when component timing fields are absent.
- Added unit coverage with a synthetic resident artifact fixture.
- Reused the Gate98 200-light sweep outputs with `--reuse-existing` to
  regenerate a component-visible sweep summary without rerunning the GPU stack.
- Updated Phase 2 documentation and algorithm source tracking.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py::test_resident_sweep_summary_extracts_registration_components tests\test_benchmarks.py::test_bench_resident_prefetch_sweep_dry_run_outputs_matrix
.\.venv\Scripts\python.exe benchmarks\bench_resident_prefetch_sweep.py --plan "C:\gpwbpp_runs\final_m38_h_200\processing_plan.json" --out "C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix" --glass-command ".\.venv\Scripts\python.exe -m glass.cli" --common-run-args-from-command "C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\run_command.txt" --common-run-arg=--resident-output-maps --common-run-arg=science --prefetch-frames 16,24 --prefetch-workers 8 --batch-frames 8 --streams 4 --wave-frames 2 --release-modes callback_queue --refill-modes immediate,queued --baseline-total-seconds 31.835984100122005 --guardrails --guardrails-pixel-verify --guardrails-pixel-verify-tile-size 4096 --guardrails-stack-scope integration --guardrails-expected-integration-engine cuda_resident_stack --max-variant-seconds 180 --max-guardrails-seconds 180 --reuse-existing
.\.venv\Scripts\python.exe -m pytest -q tests\test_benchmarks.py
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_sweep.py tests\test_benchmarks.py docs\algorithm_sources.md docs\phase2_algorithm_hardening.md
.\.venv\Scripts\glass.exe doctor --json runs\checkpoints\s2_gate_99_doctor.json
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
```

## Test Results

- Focused component tests: 2 passed in 0.29 s.
- Benchmark tests: 11 passed in 2.44 s.
- Full pytest: 305 passed in 14.40 s.
- Focused ruff and full `ruff check .`: passed.
- Native CUDA build: passed, no rebuild needed.
- `glass doctor`: passed and wrote
  `runs/checkpoints/s2_gate_99_doctor.json`.

## CUDA Status

- CUDA available: yes.
- Native extension loaded: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light Evidence

- Reused sweep output:
  `C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix`
- Regenerated summary JSON:
  `C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\resident_prefetch_sweep_summary.json`
- Regenerated summary Markdown:
  `C:\glass_runs\phase2_s2_gate_98_imported_sweep_matrix\resident_prefetch_sweep_summary.md`
- Guardrails:
  `4 / 4` variants passed after the summary regeneration.

## Component Timing Table

| Rank | Variant | Total s | Reg/warp s | Catalog s | Pixel refine s | Warp s |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `pf16_pw8_b8_s4_w2_callback_queue_rfqueued` | `15.523251` | `2.643440` | `1.068200` | `0.899447` | `0.450232` |
| 2 | `pf16_pw8_b8_s4_w2_callback_queue` | `15.811795` | `2.675019` | `1.070991` | `0.935047` | `0.448089` |
| 3 | `pf24_pw8_b8_s4_w2_callback_queue_rfqueued` | `16.077046` | `2.671790` | `1.083643` | `0.904302` | `0.450337` |
| 4 | `pf24_pw8_b8_s4_w2_callback_queue` | `16.351797` | `2.679052` | `1.091172` | `0.916525` | `0.452149` |

## Interpretation

- The current best variant remains
  `pf16_pw8_b8_s4_w2_callback_queue_rfqueued`.
- Resident registration/warp is now directly visible in the sweep table at
  about `2.64 s`.
- Within the triangle registration path, moving catalog extraction is about
  `1.07 s`, pixel refinement is about `0.90 s`, and warp is about `0.45 s`.
- This makes moving-catalog extraction and pixel refinement the clearest next
  optimization targets, with warp batching still meaningful but smaller.

## Known Limitations

- This gate changes reporting only. It does not change resident CUDA kernels,
  registration choices, accepted frames, image math, or output pixels.
- Some component fields are native/cumulative diagnostics. They should be read
  alongside the aggregate `resident_registration_warp_s` wall time.
- Existing older runs without component timing remain reportable but show blank
  component columns.

## Next Step

Start the next algorithmic gate by reducing resident triangle moving-catalog
and pixel-refinement cost, using the Gate99 component table as the baseline.

## Clean-Room Compliance

Compliant. This gate consumes GLASS-owned timing artifacts only and does not
read, copy, summarize, or rework any proprietary implementation source.
