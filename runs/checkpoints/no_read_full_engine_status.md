# No Read-Full Engine Convenience Paths Checkpoint

- Date: 2026-05-12
- Scope: Remove remaining avoidable `read_full()` convenience paths from engine-level flat normalization and registration preview generation.
- Related gates: strengthens out-of-core consistency across Gates 5, 8, and 12.

## Completed

- Updated flat median normalization to use the scratch-memmap exact median path for small and large images.
- Updated registration preview generation so `preview_scale=1` images are still filled through tile reads.
- Added regression tests that monkeypatch `FitsImageReader.read_full` to fail for:
  - flat median normalization;
  - scale-one registration previews.
- Updated memory-model documentation.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m py_compile src/glass/engine/pipeline.py src/glass/engine/registration.py tests/test_pipeline_fixture.py tests/test_cpu_registration.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_pipeline_fixture.py tests/test_cpu_registration.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `Select-String -Path src/glass/engine/*.py,src/glass/gpu/*.py -Pattern "read_full\\(|np\\.stack\\(|fits\\.getdata\\(|\\.data" -Context 1,2`

## Test Results

- Focused pipeline/registration tests: 16 passed in 4.74 s.
- Full pytest: 59 passed in 7.04 s.
- Search result: no remaining engine/gpu `read_full()` calls. The remaining `np.stack` occurrence is the intentionally retained integration rejection path.

## CUDA Status

- CUDA available: yes.
- Device 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

## Known Limitations

- Integration rejection modes still build per-tile frame stacks because sigma/winsorized rejection requires the per-pixel frame distribution.
- Some CPU baseline modules remain intentionally in-memory correctness references.
- PixInsight/WBPP black-box timing comparison remains blocked until a user-generated WBPP output and timing log are provided.

## Next Step

- Either implement a bounded multi-pass rejection mode or proceed with PixInsight/WBPP black-box timing once reference output is available.

## Clean-Room Compliance

- No PixInsight/WBPP/PJSR source files were read, copied, summarized, or modified.
- No user input directory was modified.
