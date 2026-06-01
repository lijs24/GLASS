# S2-Gate 113 Status: Resident Triangle Agreement Gate

## Gate

S2-Gate 113: Resident Triangle Agreement Gate.

## Completed Content

- Added a project-defined resident triangle agreement score:
  `pixel_ncc / (1 + max(pixel_rms_adu, 0) / rms_scale_adu)`.
- Kept default behavior audit-only; frames are rejected only when an explicit
  `cuda_triangle_min_agreement_score` plan value or CLI override is supplied.
- Added `--resident-triangle-min-agreement-score` and
  `--resident-triangle-agreement-rms-scale` to `glass run` and `glass audit`.
- Recorded agreement score/status/reason/RMS scale/threshold in per-frame
  registration warnings and resident registration artifacts.
- Extended resident registration candidate audits and compare joins to parse
  and summarize agreement scores.
- Updated Phase 2 gate documentation and algorithm-source audit notes.

## Commands Run

- `python -m pytest -q tests/test_resident_cuda_run.py::test_resident_triangle_agreement_quality_scores_pixel_refinement tests/test_cli_smoke.py::test_cli_help_commands`
- `python -m ruff check src/glass/engine/resident_cuda.py src/glass/cli.py tests/test_resident_cuda_run.py`
- `python -m pytest -q tests/test_resident_cuda_run.py::test_cli_resident_cuda_run_similarity_triangle_aligns_shifted_pair`
- `python -m ruff check src/glass/report/resident_registration_audit.py src/glass/report/resident_registration_compare.py tests/test_resident_registration_audit.py tests/test_resident_registration_compare.py tests/test_resident_cuda_run.py`
- `python -m pytest -q tests/test_resident_cuda_run.py::test_resident_triangle_agreement_quality_scores_pixel_refinement tests/test_resident_registration_audit.py tests/test_resident_registration_compare.py tests/test_cli_smoke.py::test_cli_help_commands`
- `python -m ruff check .`
- `python -m pytest -q`
- Native CUDA build through Visual Studio developer environment:
  `cmake --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel`
- `glass doctor --json C:\glass_runs\phase2_s2_gate_113_triangle_agreement\doctor_final.json`
- 200-light real-data audit-only resident CUDA run:
  `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_113_triangle_agreement\real_m38_g28x16_gt2_sep96_audit_only ... --resident-output-maps minimal`
- `glass resident-registration-audit --run C:\glass_runs\phase2_s2_gate_113_triangle_agreement\real_m38_g28x16_gt2_sep96_audit_only --out C:\glass_runs\phase2_s2_gate_113_triangle_agreement\real_m38_agreement_audit.json --markdown C:\glass_runs\phase2_s2_gate_113_triangle_agreement\real_m38_agreement_audit.md`

## Test Result

- Focused tests: passed.
- Full test suite: `317 passed in 15.51s`.
- Ruff: passed.
- Native CUDA build: passed, `ninja: no work to do`.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Doctor artifact: `runs/checkpoints/s2_gate_113_doctor.json`.

## Real-Data Artifact

- Run directory:
  `C:\glass_runs\phase2_s2_gate_113_triangle_agreement\real_m38_g28x16_gt2_sep96_audit_only`
- Audit JSON:
  `C:\glass_runs\phase2_s2_gate_113_triangle_agreement\real_m38_agreement_audit.json`
- Audit Markdown:
  `C:\glass_runs\phase2_s2_gate_113_triangle_agreement\real_m38_agreement_audit.md`
- Run elapsed time: `13.87117260042578` seconds.
- Triangle frames: `200`.
- Failed triangle frames: `0`.
- Agreement status counts: `audit_only=192`.
- Agreement score stats:
  - count: `192`
  - min: `0.0627817`
  - median: `0.5173365000000001`
  - mean: `0.5034734395833333`
  - max: `0.728413`

## Known Limitations

- The agreement score is a GLASS-defined control diagnostic, not a universal
  scientific rejection threshold.
- Default behavior remains audit-only; no new default frame rejection was
  promoted in this gate.
- The real-data run used minimal output maps to keep the gate artifact light,
  so it is not a full promotion benchmark.
- Low-score frame thresholds still need compare-gated 200-light sweeps before
  any production default changes.

## Next Step

Run a bounded agreement-threshold sweep over the 200-light benchmark, starting
with conservative thresholds below the observed median, and require frame-count,
guardrail, and strict image-compare gates before considering promotion.

## Clean-Room Compliance

Compliant. This gate used GLASS-owned source, GLASS-generated artifacts,
project-defined formulas, and user-generated benchmark data only. It did not
read, copy, summarize, or rework external proprietary implementation source and
did not modify input image directories.
