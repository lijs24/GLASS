# S2-Gate 67 Status: Acceptance Audit Resident Drift Attachment

## Gate

S2-Gate 67 - Acceptance Audit Resident Drift Attachment.

## Completed

- Added optional `glass acceptance-audit --resident-determinism-json`.
- Acceptance audit JSON now carries:
  - resident determinism source path;
  - strict resident determinism pass/fail summary;
  - resident determinism timing summary;
  - output numerical drift count;
  - max relative output RMS drift;
  - detailed `output_numerical_drifts` rows for downstream reporting.
- Acceptance audit Markdown now includes a `Resident Determinism` section.
- Existing acceptance pass/fail semantics are unchanged; resident drift evidence is informational until a later benchmark contract explicitly sets thresholds.
- HTML report can render the attached drift rows through the normal `--acceptance-audit` path.
- Updated Phase 2 plan and algorithm-source ledger for S2-Gate 67.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_acceptance_audit.py::test_acceptance_audit_cli_writes_outputs_and_returns_failure tests\test_cli_smoke.py::test_cli_report_includes_resident_artifacts
.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\manifest.json --glass-run C:\glass_runs\final_m38_h_200\glass_current_20260514_154556 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\final_m38_h_200\glass_current_20260514_154556\compare_vs_reference_scaled_coverage190.json --resident-determinism-json C:\glass_runs\phase2_s2_gate_65_200\resident_determinism_gate63_vs_fast_coarse_with_numeric_drift.json --out C:\glass_runs\phase2_s2_gate_67_200\acceptance_with_resident_drift.json --markdown C:\glass_runs\phase2_s2_gate_67_200\acceptance_with_resident_drift.md --min-active-frames 190
.\.venv\Scripts\glass.exe report --run C:\glass_runs\final_m38_h_200\glass_current_20260514_154556 --out C:\glass_runs\phase2_s2_gate_67_200\acceptance_with_resident_drift_report.html --acceptance-audit C:\glass_runs\phase2_s2_gate_67_200\acceptance_with_resident_drift.json
Select-String -Path C:\glass_runs\phase2_s2_gate_67_200\acceptance_with_resident_drift.md -Pattern "Resident Determinism|Output numerical drifts|relative_rms|H:200"
Select-String -Path C:\glass_runs\phase2_s2_gate_67_200\acceptance_with_resident_drift_report.html -Pattern "Output numerical drift|H:200|0.011916|resident"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\glass.exe doctor
```

## Test Results

- Focused acceptance/report tests: `2 passed in 0.17s`.
- Ruff: `All checks passed!`.
- Full pytest: `269 passed in 11.39s`.
- Real 200-light acceptance audit with attached resident drift: `passed`.
  - Speedup vs WBPP: `34.665737721106105x`.
  - Active weighted frames: `193`.
  - Light/bias/dark/flat counts: `200/20/20/20`.
  - Compare coverage fraction: `0.9574613308418977`.
  - Compare RMS diff: `0.001558294284488301`.
  - Compare abs diff p99: `0.00043095467146486016`.
- Attached resident output drift:
  - Drift rows: `1`.
  - Artifact key: `H:200:F000061:F000260`.
  - Field: `master_path`.
  - RMS drift: `3.7514002323150635 ADU`.
  - Mean absolute drift: `0.6422600150108337 ADU`.
  - Relative RMS to baseline std: `0.011915983618972378`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate_67_200\acceptance_with_resident_drift.json`
- `C:\glass_runs\phase2_s2_gate_67_200\acceptance_with_resident_drift.md`
- `C:\glass_runs\phase2_s2_gate_67_200\acceptance_with_resident_drift_report.html`

## CUDA

- CUDA wrapper importable: yes.
- CUDA native extension loaded: yes.
- CUDA available: yes.
- GPU 0: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.
- Package recommendation: cuda.

## Known Limitations

- Resident drift attachment is informational and does not yet participate in acceptance pass/fail checks.
- The attached drift example compares the conservative Gate63 path against the explicit fast-coarse Gate64 path; it is not a new WBPP comparison.
- The real acceptance audit body uses the previously validated `glass_current_20260514_154556` 200-light run because that run has the authoritative WBPP timing and coverage-masked compare artifact.

## Next Step

S2-Gate 68 should decide whether to formalize resident numerical drift thresholds in benchmark contracts, or continue optimizing the two largest wall-time components: I/O/upload/calibration overlap and resident registration/warp batching.

## Clean-Room

Compliant. This gate only composes GLASS-generated audit artifacts and user-generated black-box timing/output metadata. It does not read, copy, summarize, or rework PixInsight/WBPP implementation source.
