# GLASS Windows Packaging

This folder contains Windows-first release helpers. The ordinary user path is a
portable folder or installer that includes Python, GLASS, dependencies, and the
optional native CUDA module. Users should not need the CUDA Toolkit unless they
want to build GLASS from source.

Release shapes:

- `GLASS-Portable-win64.zip`: unpack and run `glass.cmd`.
- `GLASS-Setup-win64.exe`: installer built from the portable folder with Inno Setup.
- `glass-stack` Python package: CPU-capable package for Python users.
- Future `glass-cuda-cu12` package: CUDA native module wheel for NVIDIA users.

The portable builder assumes a clean checkout and writes artifacts under
`.release/windows`.
