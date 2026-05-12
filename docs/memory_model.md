# Memory Model

GPWBPP must not load all input frames into CPU RAM or GPU VRAM. Metadata stages
read only headers. Pixel stages use bounded tile or slab iteration.

`FitsImageReader` performs raw memmapped FITS tile reads and applies
`BSCALE`/`BZERO` per tile for scaled integer FITS. This avoids the Astropy
scaled-image `memmap=False` fallback in the light calibration, warp, local
normalization, and integration paths. Current master frame construction still
has a known full-frame CPU-array limitation in the high-level pipeline.

The memory model has four levels:

- Source files: immutable FITS/XISF input images.
- Host staging: small tile/slab buffers, preferably memory-mapped or streaming
  reads.
- Device staging: bounded CUDA buffers sized by VRAM budget.
- Run cache: checkpointable intermediate artifacts under the run directory.

The tile scheduler exposes rectangular tiles with stable bounds. Later gates
extend it with halos for convolution, star detection, warp interpolation, and
local normalization windows.

Every heavy stage should declare:

- input artifacts;
- output artifacts;
- tile shape;
- RAM budget;
- VRAM budget;
- checksum or freshness rule;
- resume behavior.

Failure rules:

- write `run_state.json` before returning failure;
- preserve completed artifacts;
- never modify the input directory;
- never silently skip failed frames;
- record crop boxes, masks, and coverage if geometry changes.
