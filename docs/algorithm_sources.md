# Algorithm Sources And Independence Log

This file tracks the origin of algorithms and defaults used by GLASS. Every
Phase 2 algorithm change should update the relevant row before becoming a
default path.

## Source Categories

- `clean-room derivation`: derived from general numerical or astronomical image
  processing principles.
- `paper`: derived from a cited public paper.
- `open documentation`: derived from publicly available format or API
  documentation.
- `compatible open source`: informed by code under a license compatible with
  this project. The exact project, license, and copied/non-copied status must be
  recorded.
- `black-box experiment`: derived from user-generated settings, logs, output
  files, or measured behavior from an external tool, without using its source
  code.

## Required Fields

Each entry should include:

- module
- source category
- source citation or experiment path
- formula or behavior summary
- implementation files
- tests
- default parameter origin
- independence statement
- known limitations

## Entries

| Module | Source category | Source or experiment | Summary | Implementation files | Tests | Defaults | Independence statement | Limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Phase 2 core contracts | clean-room derivation | `docs/phase2_algorithm_hardening.md` | Defines `ImageSource`, `TileWindow`, `DQMask`, `FrameTransform`, stack policies, output-map policies, and `StackRequest` as project-owned execution contracts. | `src/glass/engine/contracts.py`, `src/glass/io/image_source.py` | `tests/test_phase2_contracts.py` | Project-defined | Interfaces are derived from GLASS pipeline requirements and do not encode external implementation details. | The contracts are minimal Gate 1 forms; StackEngine behavior is added in later gates. |
| StackEngine combine policies | clean-room derivation | General weighted statistics | Mean, median, sum, and weighted mean over valid samples with optional maps. | `src/glass/engine/stack_engine.py` | `tests/test_stack_engine.py` | Project-defined | Implemented from basic statistical definitions. | CPU/tiled reference path only; default pipeline migration occurs in later gates. |
| StackEngine rejection policies | clean-room derivation / paper TBD | General robust statistics | Sigma, MAD, median sigma, percentile, min/max, and winsorized sigma rejection. | `src/glass/engine/stack_engine.py` | `tests/test_stack_engine.py` | Project-defined unless later cited | Implementation is independently written from public robust-statistics formulas and project derivation. | First-pass CPU behavior; edge-case tuning and CUDA parity are later gates. |
| StackEngine pipeline migration | clean-room derivation | `docs/phase2_algorithm_hardening.md` S2-Gate 3 | Routes CPU master calibration and non-resident CPU integration through StackEngine while retaining legacy/CUDA fast paths as fallback. | `src/glass/engine/pipeline.py`, `src/glass/engine/integration.py` | `tests/test_pipeline_fixture.py`, `tests/test_stack_engine.py` | Project-defined | Migration is an internal GLASS architecture change and preserves existing public behavior through diagnostics and fallback metadata. | Resident CUDA path is not yet StackEngine-backed; S2-Gate 3 protects the Phase 1 benchmark by keeping the CUDA fast path. |
| Data-quality mask bitfield | clean-room derivation | Project pipeline requirements | Internal bitfield for invalid, saturated, corrected, warped, LN-excluded, and rejected pixels. | `src/glass/engine/contracts.py`, `src/glass/engine/dq.py`, `src/glass/engine/pipeline.py`, `src/glass/engine/warp.py`, `src/glass/engine/local_norm.py`, `src/glass/engine/integration.py` | `tests/test_phase2_contracts.py`, `tests/test_pipeline_fixture.py` | Project-defined | Bit assignments are project-owned API and are propagated as GLASS artifacts. | S2-Gate 4 emits foundational summaries/maps; cosmetic and camera-specific flags are later gates. |
| Calibration formula and robust first pass | clean-room derivation | Standard calibration equation and robust statistics | Bias/dark/flat correction with explicit dark-bias semantics, scaling, per-flat normalization, flat floor, pedestal, overscan/trim helper, and cosmetic DQ marking. | `src/glass/cpu/calibration.py`, `src/glass/cpu/cosmetic.py`, `src/glass/engine/pipeline.py` | `tests/test_cpu_calibration.py`, `tests/test_pipeline_fixture.py` | Project-defined | Formula and first-pass robust controls are implemented from standard calibration and robust-statistics definitions. | Dark optimization and full tile-mode overscan transform remain future work. |
| Star detection and PSF metrics | paper / clean-room derivation | Stetson, P. B. 1987, "DAOPHOT - A computer program for crowded-field stellar photometry", PASP 99:191-222, doi:10.1086/131977; standard image moments | Robust background/noise estimation, thresholded local maxima, centroid and second-moment PSF estimates, median FWHM/eccentricity/star-SNR frame metrics, saturation fraction, and combined quality weighting. | `src/glass/cpu/star_detect.py`, `src/glass/cpu/metrics.py`, `src/glass/engine/quality.py`, `src/glass/engine/integration.py` | `tests/test_cpu_star_detect.py`, `tests/test_cpu_integration.py`, `tests/test_pipeline_fixture.py` | Project-defined thresholds and weight factors | The implementation is written from public photometry concepts and project-owned moment formulas; no proprietary source code is used. | It is DAOFIND-like but not a full DAOPHOT clone; deblending, aperture correction, and spatial PSF modeling remain future work. |
| Registration model ladder | clean-room derivation / paper TBD | General geometric transforms | Translation, similarity, affine, homography, robust matching, and residual validation. | TBD | TBD | Project-defined | Uses standard geometric fitting and robust estimation concepts. | Higher-order distortion models remain future work. |
| Warp interpolators | clean-room derivation | Standard interpolation kernels | Nearest, bilinear, bicubic, and Lanczos 3 interpolation through a registry. | TBD | TBD | Project-defined | Kernels implemented from public mathematical definitions. | Drizzle added later. |
| Local normalization | clean-room derivation / paper TBD | TBD | Continuous coefficient fields `O(x,y)=a(x,y)S(x,y)+b(x,y)` fitted from masked background samples. | TBD | TBD | Project-defined | Implemented as project-owned robust regression and smoothing pipeline. | Nebulosity masking needs validation. |
| Variance-aware integration | clean-room derivation / paper TBD | TBD | Per-frame or per-pixel inverse-variance weighting with variance map output. | TBD | TBD | Project-defined | Implemented from public statistical definitions. | Camera noise model calibration required. |

## Update Rule

When adding or modifying an algorithm:

1. Add or update an entry in this file.
2. Link the implementation file and tests.
3. State whether defaults are project-defined, experiment-derived, or cited.
4. Record any external data or black-box experiment used for validation.
5. Keep public user-facing claims proportional to measured evidence.
