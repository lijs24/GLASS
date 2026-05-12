# Memory Model

GPWBPP must not load all input frames into CPU RAM or GPU VRAM. Metadata stages
read only headers. Pixel stages use bounded tile or slab iteration.

`FitsImageReader` performs raw memmapped FITS tile reads and applies
`BSCALE`/`BZERO` per tile for scaled integer FITS. This avoids the Astropy
scaled-image `memmap=False` fallback in the light calibration, warp, local
normalization, and integration paths. Master bias, dark, and flat construction
also uses tile streaming in the high-level pipeline. Within each tile, master
stacking uses a fixed-size float64 accumulator instead of a 3D tile stack, so
host memory does not scale with calibration-frame count. Large
median-normalized flats use a temporary float32 `memmap` scratch file and an
in-place partition to compute an exact median without keeping the full image in
process memory.

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
