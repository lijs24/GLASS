# Gate 08 Checkpoint: CPU triangle asterism bridge

## Gate

Gate 08: Registration.

## Completed content

- Added a GPWBPP-owned CPU triangle asterism bridge:
  - local nearest-neighbor triangle descriptor generation;
  - scale-invariant side-ratio descriptor matching;
  - similarity/affine hypothesis fitting;
  - one-to-one inlier scoring and iterative refit.
- Added tests for:
  - synthetic known similarity transform with an outlier;
  - comparison against the optional MIT-licensed `astroalign` backend on the same small star-field image pair.
- Updated `docs/registration_model.md` to record the clean-room bridge and its intended CUDA migration role.

## Commands run

- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cpu_registration.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check src\\gpwbpp\\cpu\\registration.py tests\\test_cpu_registration.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -c "import gpwbpp_cuda as c; print('cuda_available', c.cuda_available()); print(c.list_devices())"`
- `git diff --check`

## Test results

- Targeted registration tests: `12 passed in 0.42s`.
- Ruff on touched Python files: `All checks passed!`.
- Full pytest suite: `153 passed in 7.60s`.
- `git diff --check`: no whitespace errors; only Windows CRLF conversion warnings from Git.

## CUDA availability

CUDA is available.

- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- Total VRAM: 97886 MiB
- Native backend: available

## Known limitations

- This is a CPU registration bridge, not the final pure-GPU StarAlignment replacement.
- The descriptor model is triangle-based; PixInsight public documentation describes newer polygonal descriptors such as pentagons.
- The current bridge validates a clean migration target for CUDA local-KNN, descriptor matching, hypothesis scoring, and refit. It does not yet replace resident GPU registration in the 200-light benchmark.

## Next step

Port the triangle asterism bridge to CUDA-resident catalogs:

- generate local KNN neighborhoods on device;
- emit triangle descriptors on device;
- match descriptor pairs on device;
- score similarity hypotheses with mutual inliers;
- keep pixel warp and integration resident on GPU.

## Clean-room compliance

Compliant. No PixInsight/WBPP/PJSR source code was read or used. PixInsight StarAlignment behavior was treated as public documentation/forum black-box context only. The implementation is GPWBPP-owned and was checked against optional open-source `astroalign` behavior only for validation.
