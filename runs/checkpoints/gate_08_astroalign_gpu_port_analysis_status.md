# Gate 08 Increment: Astroalign GPU Port Analysis

## Gate

Gate 08 - Registration.

## Completed Content

- Inspected the installed open-source `astroalign` package as a permissible correctness bridge.
- Confirmed local package:
  - version: `2.6.2`
  - source file: `.venv\Lib\site-packages\astroalign.py`
  - license metadata: MIT License
- Documented the algorithmic structure in `docs/registration_model.md`:
  - SEP background/source extraction;
  - top flux-limited source catalog;
  - local KD-tree nearest-neighbor selection;
  - local triangle asterism generation;
  - side-ratio invariant construction;
  - KD-tree invariant matching;
  - RANSAC similarity fitting;
  - duplicate source-to-target pair reduction by reprojection error;
  - skimage warp as the CPU pixel-resampling path.
- Recorded a staged GPU migration plan:
  1. Keep astroalign/SEP as the CPU correctness baseline.
  2. Port triangle asterism generation, invariant matching, batched fit, and inlier scoring to resident CUDA.
  3. Extend descriptors from triangles to quads/pentagons for PixInsight-like robustness.

## Commands Run

- `python` metadata probe through the project venv:
  - import `astroalign`
  - report `astroalign.__file__`
  - report `importlib.metadata.version("astroalign")`
  - report license metadata
- Source structure inspection:
  - `Select-String -Path .venv\Lib\site-packages\astroalign.py -Pattern "def |class |NUM_NEAREST|MIN_MATCH|PIXEL_TOL|triangle|asterism|KDTree|RANSAC|estimate_transform|find_transform"`
- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Full suite: `151 passed in 9.76s`.
- Documentation/analysis-only increment.
- No runtime behavior changed.

## CUDA Availability

- CUDA is available.
- This increment defines the next CUDA registration migration plan but does not add kernels.

## Known Limitations

- Astroalign uses triangle asterisms; PixInsight public material describes newer polygonal descriptors as more robust.
- Astroalign's CPU implementation is a bridge, not the final GPWBPP matcher.
- The next real speed target requires implementing the descriptor/hypothesis scoring kernels, not just documenting them.

## Next Step

Add a compact star-catalog golden test that compares astroalign's matched control points/matrix with a GPWBPP-owned triangle descriptor implementation on fixed synthetic and real calibrated crops. Then port the expensive parts to CUDA.

## Clean-Room Compliance

- Only MIT-licensed open-source astroalign code was inspected.
- PixInsight/WBPP/PJSR source was not read or modified.
- The PixInsight StarAlignment model remains based only on public documentation/discussion and black-box behavior.
