# S2-Gate 616 Status: Resident Warp Chunk Capacity Retune

## Gate

- Gate: S2-Gate 616
- Status: green
- Branch: `main`
- Date: 2026-06-25

## Completed Contents

- Retuned resident runtime presets:
  - `throughput-v3-io`: `resident_warp_chunk_capacity_frames=8`;
  - `throughput-v4-native-completion`: `resident_warp_chunk_capacity_frames=8`.
- Preserved explicit `--resident-warp-chunk-capacity-frames` overrides.
- Preserved memory-admission reduction/disable behavior for tighter explicit
  VRAM budgets.
- Did not change registration math, matrices, Lanczos3 warp interpolation,
  frame admission, DQ semantics, local normalization, rejection, or integration.
- Updated CLI preset tests, Phase 2 plan, algorithm-source log, and known
  limitations.

## Real 200-Light Evidence

Probe root:

- `C:\glass_runs\phase2_s2_gate616_warp_chunk_capacity`

Capacity matrix:

| Chunk capacity | Chunk count | Native warp total | Native warp sync | Kernel enqueue | Observed workspace | Estimated peak |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `8` | `24` | `0.4869027 s` | `0.4660586 s` | `0.0178497 s` | `2.2967 GiB` | `49.6084 GiB` |
| `16` | `12` | `0.5034751 s` | `0.4630237 s` | `0.0347686 s` | `4.5934 GiB` | `51.9051 GiB` |
| `32` | `6` | `0.5400121 s` | `0.4606894 s` | `0.0698597 s` | `9.1868 GiB` | `56.4985 GiB` |
| `64` | `3` | `0.6176782 s` | `0.4617681 s` | `0.1377537 s` | `18.3735 GiB` | `65.6852 GiB` |
| `96` | `2` | `0.7057142 s` | `0.4711825 s` | `0.2082498 s` | `27.5602 GiB` | `74.8720 GiB` |
| `128` | `2` | `0.7888434 s` | `0.4706606 s` | `0.2782146 s` | `36.7470 GiB` | `84.0587 GiB` |

Default postpatch run:

- Baseline:
  `C:\glass_runs\phase2_s2_gate615_ln_batch_apply\real_200_default_regression`
- Candidate:
  `C:\glass_runs\phase2_s2_gate616_warp_chunk_capacity\real_200_default_chunk8_postpatch`
- Passing regression gate:
  `C:\glass_runs\phase2_s2_gate616_warp_chunk_capacity\resident_regression_gate_default_chunk8_vs_gate615.json`
- Markdown:
  `C:\glass_runs\phase2_s2_gate616_warp_chunk_capacity\resident_regression_gate_default_chunk8_vs_gate615.md`

Key results:

- Regression gate passed.
- Candidate/baseline elapsed ratio: `0.9934991826007156`.
- Determinism differences: artifact `0`, frame signatures `0`,
  registration `0`, frame accounting `0`, output pixels `0`, numerical drift
  `0`.
- Frame admission: `193 / 200` active, `7` masked.
- Default native chunk frames: `32 -> 8`.
- Native warp total: `0.5400121 s -> 0.4868301 s`.
- Native warp kernel enqueue: `0.0698597 s -> 0.0168166 s`.
- Observed chunked-warp workspace:
  `9.186752557754517 GiB -> 2.296694040298462 GiB`.
- Estimated peak memory:
  `56.49848845601082 GiB -> 49.608429938554764 GiB`.

## Commands Run

- Real 200-light capacity probes:
  - `glass run ... --resident-warp-chunk-capacity-frames 64`
  - `glass run ... --resident-warp-chunk-capacity-frames 96`
  - `glass run ... --resident-warp-chunk-capacity-frames 128`
  - `glass run ... --resident-warp-chunk-capacity-frames 16`
  - `glass run ... --resident-warp-chunk-capacity-frames 8`
- Determinism audits against Gate615 for 64/96/128 and regression gates for
  8/16.
- Postpatch default real 200-light run without an explicit chunk override.
- `glass resident-regression-gate --baseline-run C:\glass_runs\phase2_s2_gate615_ln_batch_apply\real_200_default_regression --candidate-run C:\glass_runs\phase2_s2_gate616_warp_chunk_capacity\real_200_default_chunk8_postpatch --max-elapsed-ratio 1.15 --min-active-frame-count 190 --max-masked-frame-count 10 --fail-on-failure`
- `python -m pytest -q tests\test_cli_smoke.py -k "resident_runtime_preset or chunk_capacity_from_admission"`
- `python -m pytest -q tests\test_resident_cuda_run.py -k "memory_admission or matrix_batch"`
- `python -m ruff check src\glass\cli.py tests\test_cli_smoke.py`
- `python -m pytest -q`
- `git diff --check`

## Test Results

- CLI preset/admission focused set: `12 passed, 63 deselected`.
- Resident memory/matrix-batch focused set: `9 passed, 107 deselected`.
- Combined focused rerun: `9 passed, 182 deselected`.
- Ruff: `All checks passed`.
- Full pytest: `1295 passed in 52.88 s`.
- `git diff --check`: no whitespace errors; only CRLF conversion warnings.

## CUDA

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Multiprocessors: `188`.
- Native backend: available.

## Known Limits

- This is a default scheduling retune, not a new warp kernel.
- Larger chunks remain available as explicit profiling overrides, but the
  current Lanczos3 batch warp is not faster just because more VRAM is used.
- The larger next step is safe resident warp kernel scheduling work, such as
  multi-stream chunk execution with correct coverage accumulation semantics.

## Clean-Room Compliance

- Input image directories were read-only.
- No PixInsight/WBPP/PJSR source code was read, copied, summarized, or reworked.
- The implementation is based on GLASS-owned runtime preset/admission code,
  GLASS artifacts/tests, and user-owned benchmark data.

## Next Step

- Continue resident registration/warp hardening by targeting kernel scheduling
  itself rather than only retuning chunk size.
