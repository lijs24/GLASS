# Gate 08 Increment: StarAlignment Clean-Room Analysis

## Gate

Gate 08 - Registration.

## Completed Content

- Added a clean-room StarAlignment reference section to `docs/registration_model.md`.
- Summarized public, non-source information relevant to GLASS registration:
  - triangle similarity as the older descriptor model;
  - polygonal descriptors including quads through octagons, with pentagons described as the default;
  - local coordinate hash construction from the most distant pair of polygon stars;
  - RANSAC as robust false-match rejection and registration-model optimization;
  - thin-plate / surface-spline distortion correction;
  - mirror/specular-transform caveat for polygonal descriptors.
- Recorded the GLASS implementation implication: move beyond simple pair-offset voting toward GPU star catalogs, quad/pentagon descriptors, batched GPU hypothesis scoring, interim CPU RANSAC control, and resident CUDA warp.

## Sources

- Public PixInsight tutorial: `https://www.pixinsight.com/tutorials/sa-distortion/index.html`
- Public PixInsight forum discussion on dissimilar/mirrored images: `https://pixinsight.com/forum/index.php?threads%2Fstaralignment-of-dissimilar-images.17826%2F=`
- Public PixInsight forum discussion referencing StarAlignment RANSAC behavior: `https://pixinsight.com/forum/index.php?threads%2Fstaralignment-confusion.17047%2F=`

## Commands Run

- `.venv\Scripts\python.exe -m pytest -q`

## Test Results

- Full suite: `151 passed in 11.08s`
- Documentation-only increment; no source behavior changed.

## CUDA Availability

- CUDA is available.
- This documentation increment is backend-independent.

## Known Limitations

- This is not a claim of source-code equivalence with PixInsight.
- Only public documentation/discussion and black-box behavior are acceptable evidence.
- Exact StarAlignment internals remain proprietary and are not used.

## Next Step

Implement or integrate an open-source asterism/descriptor matcher as the CPU correctness bridge, then port descriptor construction and hypothesis scoring to resident CUDA.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source was read or modified.
- No proprietary function/class names or source structure were copied.
- The content is a high-level algorithmic summary based on public materials.
