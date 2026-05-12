# GPWBPP Architecture

GPWBPP is a clean-room WBPP-like astronomical preprocessing pipeline. It is
organized as a Python control plane, CPU scientific baseline, optional CUDA
backend, and auditable run directory.

The control plane owns:

- metadata scanning without full pixel reads;
- grouping and calibration matching;
- processing plan generation;
- resumable run state;
- artifact manifests and reports;
- backend selection and capability checks.

The CPU baseline owns correctness-first implementations for master frames,
calibration, star detection, registration helpers, local normalization helpers,
and integration. CUDA kernels are added only after a CPU reference exists.

The optional CUDA backend owns device discovery, tile memory scheduling,
calibration kernels, reductions, warp, local normalization, and integration
accumulators. It must remain optional so CPU-only installs and tests work.

The pipeline stages are:

1. scan
2. plan
3. master calibration frames
4. light calibration
5. quality measurement
6. registration
7. warp/register tiles
8. local normalization
9. integration
10. report
11. compare

All heavy pixel stages are designed for tile/slab streaming. Input directories
are read-only. Output artifacts, logs, caches, and state files live under a run
directory.

Capability flags are intentionally explicit. Early gates expose placeholders or
CPU baselines rather than claiming completed CUDA behavior.

Clean-room compliance is a core architecture constraint. The project does not
read, copy, summarize, or rework official PixInsight WBPP/PJSR source code.
PixInsight may only be used later as a black-box reference through
user-generated logs, settings, and output files.

