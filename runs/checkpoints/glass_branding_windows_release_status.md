# GLASS Branding and Windows Release Checkpoint

## Gate

Release-preparation checkpoint after the GLASS naming decision.

## Completed Content

- Renamed the Python package, CLI, native CUDA wrapper, C++ include namespace, PixInsight front-end filename, docs, reports, tests, benchmarks, and checkpoint text to GLASS naming.
- Set the product name to `glass-stack` and the CLI entry point to `glass`.
- Added `glass doctor` for Python, package, CUDA wrapper, native backend, and device diagnostics.
- Added Windows release helpers under `packaging/windows/`:
  - portable folder and zip builder;
  - wheel/sdist builder;
  - Inno Setup installer template;
  - Windows release notes.
- Added `MANIFEST.in` for source distribution hygiene.
- Added project overview and Windows release documentation.
- Renamed the active branch to `glass-cuda-release`.
- Rechecked legacy project-token and legacy local-path searches: zero tracked matches.

## Commands Run

- `python -m pip install -e .[dev,report]`
- `glass doctor --allow-cpu-only`
- Native CUDA CMake configure and build for `_glass_cuda_native`
- `python -m ruff check .`
- `python -m pytest -q`
- `python -m build --wheel --sdist`
- Git tracked-content and tracked-path legacy token checks

## Test Results

- Editable install: passed.
- Native CUDA module build: passed.
- Doctor command: passed.
- Ruff: passed.
- Pytest: `184 passed`.
- Wheel and source distribution build: passed.

## CUDA Status

- CUDA wrapper importable: yes.
- Native extension loaded: yes.
- CUDA available: yes.
- Device observed by `glass doctor`: NVIDIA RTX PRO 6000 Blackwell Workstation Edition, compute capability 12.0, 97886 MiB VRAM.

## Known Limitations

- The produced Python wheel is CPU-portable; the Windows portable builder can bundle the native CUDA module for this workstation.
- A polished public binary release still needs versioned CI artifacts, code signing, and a separate CUDA-runtime compatibility matrix.
- The outer local workspace directory name is not part of tracked project content.

## Next Step

- Build and test the Windows portable package end to end, then decide whether the first public GPU distribution should be a portable zip, installer, or paired CPU wheel plus CUDA plugin wheel.

## Clean-Room Compliance

- Compliant.
- No PixInsight/WBPP/PJSR official source, script internals, or installation directories were read or modified for this checkpoint.
- PixInsight/WBPP references remain limited to black-box comparison and user-generated outputs.
