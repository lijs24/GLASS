# Gate 08 Resident Grid-NMS Similarity Checkpoint

## Gate
Gate 08: Registration

## Completed contents
- Added resident CUDA star catalog selectors to `ResidentCalibratedStack`:
  - `star_top_nms_candidates`
  - `star_grid_top_nms_candidates`
- These selectors run directly from resident GPU frame memory and avoid downloading full calibrated frames to CPU.
- Exposed the new resident methods through the Python `glass_cuda.ResidentCalibratedStack` wrapper.
- Updated `similarity_cuda_catalog` resident registration to use resident grid-top-NMS catalogs when `--resident-star-grid-cols/rows` are provided, falling back to top-NMS/top-flux as needed.
- The resident registration selector now checks the native extension method availability before choosing grid/top-NMS, so older native builds can still fall back cleanly.
- Added tests for the new resident NMS catalog methods and updated resident similarity registration smoke coverage.
- Rebuilt the native CUDA extension through Visual Studio BuildTools Developer Command Prompt.
- Ran a real full-resolution two-light M38 validation using resident grid-top-NMS similarity registration.

## Commands run
- `cmd.exe /c '"C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64 -host_arch=x64 && "<repo>\\.venv\\Scripts\\cmake.exe" --build build\\native-cuda --target _glass_cuda_native -j 8'`
- `.\\.venv\\Scripts\\python -m pytest -q tests/test_gpu_star_detect.py::test_resident_stack_star_top_nms_candidates_from_device_frame tests/test_gpu_star_detect.py::test_resident_stack_star_grid_top_nms_candidates_from_device_frame tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_catalog_aligns_shifted_pair`
- `.\\.venv\\Scripts\\python -m pytest -q tests/test_gpu_star_detect.py tests/test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\python -m pytest -q`
- Real pair run:
  - `.\\.venv\\Scripts\\glass.exe run --plan C:\\glass_runs\\final_m38_h_200\\glass_resident_similarity_catalog_pair_grid96\\processing_plan.json --out C:\\glass_runs\\final_m38_h_200\\glass_resident_similarity_catalog_pair_grid96 --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection none --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_catalog --resident-star-threshold 0 --resident-star-max-candidates 96 --resident-star-tolerance-px 3.0 --resident-registration-max-shift 24 --resident-ncc-sample-stride 4 --resident-subpixel-radius-steps 4 --resident-subpixel-step 0.25 --resident-star-prior ncc --resident-star-prior-radius-px 4 --resident-star-grid-cols 24 --resident-star-grid-rows 16 --reference-frame-id LIGHT_H_0001`

## Test results
- Resident NMS/similarity targeted tests: `3 passed in 0.24s`.
- Star detect + resident run tests: `18 passed in 0.75s`.
- Full test suite: `147 passed in 7.28s`.

## Real-data validation
- Input plan: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_pair_grid96\processing_plan.json`
- Output run: `C:\glass_runs\final_m38_h_200\glass_resident_similarity_catalog_pair_grid96`
- Real full-resolution frames: `S000021` reference and `S000022` moving, shape `6422x9600`.
- Resident registration mode: `similarity_cuda_catalog`.
- Catalog selector: `resident_grid_top_nms`.
- Star max candidates: `96`.
- Similarity top-k: `32`.
- Moving frame result:
  - status: `ok`
  - inliers: `64`
  - fit RMS: `0.8003756403923035 px`
  - resident matrix translation: `(0.8243589997291565, -0.410442054271698)`
  - astroalign preview matrix translation for same frame: `(1.2814144144840611, -0.28484174701270604)`
  - translation delta vs astroalign: `0.4739990393875615 px`
  - pixel NCC: `0.97689`
  - per-frame resident registration mean: `19.385316799976863 s`

## CUDA availability
- CUDA available: yes.
- Native backend loaded: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

## Known limitations
- `similarity_cuda_catalog` still transfers compact star catalog arrays through Python for the similarity fit; full calibrated image pixels remain resident on GPU.
- Real-data accuracy now reaches the prior strict translation-delta threshold on the tested adjacent pair, but broader 12/50/200-light validation still needs star-core guarded selection or a grid-NMS resident large-set benchmark.
- Structured resident similarity diagnostics are still stored as warnings; a dedicated JSON diagnostics block should replace this before long production runs.
- Affine/homography resident fitting remains future work.

## Next step
- Add resident star-core preselection/guard to the production `similarity_cuda_catalog` mode, then rerun a 12-light real subset before scaling back to the 200-light benchmark.

## Clean-room compliance
- Compliant.
- No PixInsight/WBPP/PJSR source, script internals, or installation directories were read or modified.
- The work reused GLASS CUDA kernels and clean-room catalog/pixel metric registration logic.
