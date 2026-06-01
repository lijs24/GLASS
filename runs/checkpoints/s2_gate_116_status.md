# S2-Gate 116 Status: Agreement Rejection Triage

## Gate

- Gate: S2-Gate 116
- Completed at: 2026-06-01T12:15:32+08:00
- Scope: add a reusable triage artifact for agreement-threshold candidate
  audits and run it over the S2-Gate 115 real 200-light sweep.

## Completed

- Added `glass resident-registration-triage`.
- Added `src/glass/report/resident_registration_triage.py`.
- Added focused tests in `tests/test_resident_registration_triage.py`.
- Updated `docs/phase2_algorithm_hardening.md` with S2-Gate 116.
- Updated `docs/algorithm_sources.md` with the triage source and result.
- Ran triage against the S2-Gate 115 audit-only baseline and the `0.05` / `0.1`
  threshold candidate audits.

## Commands

```powershell
.\.venv\Scripts\python.exe -m ruff check src\glass\report\resident_registration_triage.py src\glass\cli.py tests\test_resident_registration_triage.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_resident_registration_triage.py

glass resident-registration-triage `
  --baseline-audit C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\candidate_audits\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agrs200_candidate_audit.json `
  --candidate-audit C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\candidate_audits\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agr0p05_agrs200_candidate_audit.json `
  --candidate-audit C:\glass_runs\phase2_s2_gate_115_agreement_threshold_sweep\candidate_audits\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agr0p1_agrs200_candidate_audit.json `
  --out C:\glass_runs\phase2_s2_gate_116_agreement_rejection_triage\resident_registration_triage.json `
  --markdown C:\glass_runs\phase2_s2_gate_116_agreement_rejection_triage\resident_registration_triage.md

.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
cmd.exe /c 'call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 && .\.venv\Scripts\cmake.exe --build build\native-cuda-glass --config Debug --target _glass_cuda_native --parallel'
glass doctor --json runs\checkpoints\s2_gate_116_doctor.json
```

## Real Triage Result

- Baseline: `pf16_pw8_b8_s4_w2_callback_queue_rfqueued_agrs200`.
- Candidate `0.05`:
  - Extra rejected frames: 1.
  - Extra rejected frame id: `F000208`.
  - Candidate score/reason: `0.0337921`, agreement gate failed.
  - Baseline score for the same frame: `0.431946`.
  - Reference catalog signature match: false.
  - Selected fit signature changes among common frames: 192.
- Candidate `0.1`:
  - Extra rejected frames: 4.
  - Extra rejected frame ids: `F000083`, `F000087`, `F000259`, `F000260`.
  - Reference catalog signature match: false.
  - Selected fit signature changes among common frames: 192.
- Recommendation: `deterministic_catalog_required`.

The S2-Gate 115 threshold sweep is therefore not a clean threshold-only
experiment. Agreement filtering rejected additional frames, but the candidate
runs also changed reference catalog and selected-fit signatures versus the
audit-only baseline. The next step should stabilize resident catalog
determinism before promoting or retuning agreement thresholds.

## Artifacts

- Triage JSON:
  `C:\glass_runs\phase2_s2_gate_116_agreement_rejection_triage\resident_registration_triage.json`
- Triage Markdown:
  `C:\glass_runs\phase2_s2_gate_116_agreement_rejection_triage\resident_registration_triage.md`
- Doctor:
  `runs\checkpoints\s2_gate_116_doctor.json`

## Test Result

- Focused `ruff`: passed.
- Focused pytest: `2 passed in 0.35s`.
- Full `ruff check .`: passed.
- Full `python -m pytest -q`: `319 passed in 57.70s`.
- Native CUDA build: passed, `ninja: no work to do`.
- `glass doctor`: passed.

## CUDA

- CUDA wrapper importable: true.
- CUDA native extension loaded: true.
- CUDA available: true.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- Triage is diagnostic only; it does not change registration, scoring,
  rejection, or integration behavior.
- It compares audit artifacts. It does not read image pixels or decide whether
  an individual rejected frame is scientifically bad.
- The observed signature drift shows that the S2-Gate 115 threshold comparison
  is mixed with resident catalog nondeterminism.

## Next Step

- S2-Gate 117 should add a deterministic resident catalog mode to the current
  high-throughput grid/NMS path or force the existing deterministic mode through
  the sweep command, then rerun a small determinism audit before another
  agreement-threshold benchmark.

## Clean-Room Compliance

- This gate used GLASS-owned audit JSON and benchmark artifacts only.
- No PixInsight or WBPP/PJSR source code was read, copied, summarized, or
  modified.
- Original image directories remained read-only.
