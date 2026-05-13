# Gate 11 Status: Winsorized Sigma Rejection Semantics

Gate: 11 incremental resident CUDA integration.

Completed content:
- Corrected `winsorized_sigma` semantics in the CPU baseline and resident CUDA
  backend.
- Previous behavior clamped rejected values and included them in the final
  average. The new behavior:
  1. computes first-pass mean/std thresholds over finite, positive-weight
     samples;
  2. clamps samples only for a winsorized statistics pass;
  3. derives final low/high sigma thresholds from the winsorized mean/std;
  4. rejects original samples outside those thresholds;
  5. integrates only accepted original samples.
- Resident CUDA rejection maps, coverage map, and weight map now reflect final
  accepted samples for `winsorized_sigma`.
- The mode remains documented as an approximation, not a verified
  PixInsight-equivalent robust WSC implementation.

Commands run:
- Rebuilt native CUDA extension with CMake/Ninja, Visual Studio Build Tools, and
  CUDA Toolkit 13.2.
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_cpu_integration.py tests\\test_cuda_resident_stack.py tests\\test_resident_cuda_run.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\python.exe -m glass.cli run --plan C:\\glass_runs\\final_m38_h_200\\processing_plan.json --out C:\\glass_runs\\final_m38_h_200\\glass_resident_wsc_reject_flatfloor005_align_preview_run --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration translation_preview --reference-frame-id F000196`
- `.\\.venv\\Scripts\\python.exe -m glass.cli compare --glass C:\\glass_runs\\final_m38_h_200\\glass_resident_wsc_reject_flatfloor005_align_preview_run\\integration\\resident_master_H.fits --reference C:\\glass_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\master\\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\\glass_runs\\final_m38_h_200\\wsc_reject_flatfloor005_align_preview_scaled_resident_vs_wbpp_compare.html --glass-time-seconds 78.78527250001207 --reference-time-seconds 1092.541 --glass-label "GLASS resident CUDA WSC-reject flat-floor 0.05 translation-preview" --reference-label "PixInsight WBPP FastIntegration" --glass-scale 0.000015259021896696421 --clip-low 0 --clip-high 1`
- `.\\.venv\\Scripts\\python.exe -m glass.cli report --run C:\\glass_runs\\final_m38_h_200\\glass_resident_wsc_reject_flatfloor005_align_preview_run --out C:\\glass_runs\\final_m38_h_200\\glass_resident_wsc_reject_flatfloor005_align_preview_run\\report.html`

Test results:
- Targeted WSC/resident tests: 13 passed in 0.95 s.
- Full test suite: 76 passed in 5.57 s.

Real-data run results:
- Dataset: M38 H, 200 lights plus 20 bias, 20 dark, 20 flats.
- GLASS resident elapsed time: 78.78527250001207 s.
- WBPP black-box elapsed time: 1092.541 s.
- Raw speedup vs WBPP: 13.867325266912449x.
- Resident integration kernel time: 0.3708972000167705 s.
- Registration preview estimated `(0, 0)` integer shifts for all frames.

Rejection map diagnostics:
- Coverage min/max/mean: 181 / 200 / 198.8712615966797.
- Low rejection map sum: 436196.
- High rejection map sum: 69164248.
- Weight map min/max/mean: 181 / 200 / 198.8712615966797.

Comparison results:
- Shape match: yes.
- Scale applied to GLASS before comparison: `1 / 65535`.
- RMS diff: 0.013263855091108735.
- Relative RMS diff: 0.9910878448147922.
- Median absolute diff: 0.00011119607370346785.
- P90 absolute diff: 0.00030821096152067184.
- P99 absolute diff: 0.005503315764944989.
- P99.9 absolute diff: 0.2105630854975903.
- Max absolute diff: 0.9981225616065785.

CUDA availability:
- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- Reported VRAM: 97886 MiB.

Known limitations:
- This is still not a full PixInsight-equivalent WSC implementation. Remaining
  unknowns include exact robust scale estimator, finite-sample correction,
  iteration/cutoff behavior, and any additional WBPP/ImageIntegration policies.
- The current comparison still does not prove final master parity. The largest
  remaining gaps are WBPP's 193/200 accepted-frame policy, cosmetic correction,
  exact rejection behavior, Local Normalization, and output scaling/crop policy.

Next step:
- Add frame quality/rejection diagnostics to identify the seven WBPP-excluded
  frames and reproduce an explicit accepted-frame mask in GLASS.

Clean-room compliance:
- Compliant. The implementation uses public statistical concepts and
  project-owned code. No official WBPP/PJSR source was read or copied.
