# S2 Gate 44 Status: Optimization Guidance Contract

## Gate

S2-Gate 44: Optimization Guidance Contract

## Completed Content

- Added `src/glass/report/optimization_guide.py`.
- Acceptance-audit JSON now includes a machine-readable
  `optimization_guidance` section.
- Acceptance-audit Markdown now includes an `Optimization Guidance` section
  with:
  - primary target
  - exception-frame context
  - ranked target rows
  - concrete next action per target
- HTML reports now include an `Optimization guidance` section and navigation
  anchor.
- Guidance ranks these resident optimization targets:
  - resident registration/warp batching
  - I/O + upload + calibration overlap
  - output-map write policy
  - resident master-frame cache
- Cumulative FITS/decode worker timings remain informational and do not outrank
  wall-clock stages.
- Added timing baseline diagnostics to the strict audit-map 200-light benchmark
  contract so audit-map runs can produce the same optimization guidance while
  preserving the existing rejection-map rounding tolerance.
- Updated Phase 2 planning and algorithm-source documentation.

## Commands Run

- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\optimization_guide.py src\\glass\\report\\acceptance_audit.py src\\glass\\report\\html_report.py`
- `.\\.venv\\Scripts\\python.exe -m ruff check src\\glass\\report\\optimization_guide.py src\\glass\\report\\acceptance_audit.py src\\glass\\report\\html_report.py tests\\test_acceptance_audit.py tests\\test_cli_smoke.py`
- `.\\.venv\\Scripts\\python.exe -m pytest -q tests\\test_acceptance_audit.py tests\\test_cli_smoke.py::test_cli_report_includes_resident_artifacts`
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
- `.\\.venv\\Scripts\\python.exe -m pytest -q`
- `.\\.venv\\Scripts\\glass.exe acceptance-audit --manifest "C:\\gpwbpp_runs\\final_m38_h_200\\manifest.json" --glass-run "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531" --wbpp-result "C:\\gpwbpp_runs\\final_m38_h_200\\pixinsight_wbpp_blackbox\\wbpp_blackbox_result.json" --compare-json "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\s2_gate_32_compare.json" --benchmark-contract benchmarks\\phase2_m38_h_200_audit_maps_contract.json --out "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\phase2_contract_acceptance_audit_s2_gate_44.json" --markdown "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\phase2_contract_acceptance_audit_s2_gate_44.md"`
- `.\\.venv\\Scripts\\glass.exe report --run "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531" --acceptance-audit "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\phase2_contract_acceptance_audit_s2_gate_44.json" --out "C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\s2_gate_44_report.html"`
- `.\\.venv\\Scripts\\python.exe -c "from glass.io.json_io import read_json; p=r'C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\phase2_contract_acceptance_audit_s2_gate_44.json'; a=read_json(p); g=a['optimization_guidance']; print(a['status'], a['performance_regression']['status']); print('primary', g['primary_target']); [print(t['rank'], t['target_id'], t['current_s'], t['baseline_s'], t['factor'], t['status']) for t in g['targets']]; print('exceptions', g['exception_context'])"`
- `.\\.venv\\Scripts\\python.exe -c "from glass.capabilities import capability_report; import json; print(json.dumps(capability_report(), indent=2))"`
- `.\\.venv\\Scripts\\python.exe -c "import glass_cuda, json; print(json.dumps(glass_cuda.get_device_info(0), indent=2))"`

## Test Results

- Focused tests: `10 passed in 0.36s`
- Full pytest: `257 passed in 11.66s`
- Ruff: all checks passed

## CUDA Availability

- CUDA extension importable: yes
- CUDA available: yes
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB
- Native resident stack available: yes

## Real Artifact Validation

- Real GLASS run directory:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531`
- Regenerated acceptance audit JSON:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\phase2_contract_acceptance_audit_s2_gate_44.json`
- Regenerated acceptance audit Markdown:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\phase2_contract_acceptance_audit_s2_gate_44.md`
- Regenerated HTML report:
  `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531\s2_gate_44_report.html`
- Acceptance audit status: passed
- Performance diagnostics status: regressed, non-blocking
- Speedup vs external reference: `34.3178020369665`
- Primary optimization target: `resident_registration_warp`
- Ranked targets from real audit:
  - `resident_registration_warp`: current `12.395901901181787 s`, baseline
    `10.903585300431587 s`, factor `1.1368647614185337`, status `ok`
  - `io_upload_calibration_pipeline`: current `7.5520693003199995 s`,
    baseline `15.546634200029075 s`, factor `0.4857687653258012`, status `ok`
  - `output_write_policy`: current `2.5700724003836513 s`, baseline
    `0.9690760000376031 s`, factor `2.6520854920397623`, status `regressed`
  - `resident_master_cache`: current `0.591232500039041 s`, baseline
    `9.85976749996189 s`, factor `0.05996414216068749`, status `ok`
- Exception context: 7 zero-weight frames, dominant stage `integration`.

## Known Limitations

- This gate is diagnostic-only and does not change kernels, scheduling,
  accepted frame counts, or output pixels.
- Target ranking is based on known resident timing keys and selected
  wall-clock stages; deeper CUDA event profiling is still future work.
- Output write is marked as regressed because this audit-map run writes full
  diagnostic maps; speed-oriented science/minimal policies should still be used
  when the validation maps are not required.
- The guidance names optimization direction, not the exact implementation plan
  for the next kernel/scheduler change.

## Next Step

S2-Gate 45 should turn the primary target into implementation work: reduce
resident registration/warp wall time by batching more of star detection,
descriptor scoring, pixel refinement, and warp orchestration on the GPU, while
keeping the 200-light benchmark frame counts and image agreement stable.

## Clean-Room Compliance

Compliant. The gate uses GLASS-owned timing, report, resident, and
frame-accounting artifacts plus user-generated benchmark outputs only. No
official PixInsight/WBPP/PJSR source code was read, copied, or summarized.
