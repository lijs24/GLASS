# S2 Gate 490 Status: Post-Cleanup Real 200-Light A/B Regression

## Gate

S2-Gate490 records a real 200-light regression after C-drive cleanup. The goal
was to free local workspace space without damaging the active 200-light A/B
evidence chain, then immediately re-run the current default resident CUDA stack
path against the same PixInsight/WBPP black-box reference.

## Cleanup

- Preserved:
  - `C:\gpwbpp_runs\final_m38_h_200\input`
  - `C:\gpwbpp_runs\final_m38_h_200\processing_plan.json`
  - `C:\gpwbpp_runs\final_m38_h_200\manifest.json`
  - `C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox`
  - `C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache`
- Removed only generated legacy experiment directories matching
  `C:\gpwbpp_runs\final_m38_h_200\gpwbpp_*`.
- Removed directory count: 81.
- Reclaimed size reported by cleanup command: 268.08 GiB.
- C-drive free space after cleanup: 294.09 GiB at cleanup time; 292.95 GiB
  after the Gate490 A/B artifacts were written.

## Real 200-Light Run

Run root:

`C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real`

GLASS run:

`C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\runs\default_runtime_stack`

Command:

```powershell
.\.venv\Scripts\glass.exe run `
  --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json `
  --out C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\runs\default_runtime_stack `
  --until-stage integration `
  --local-normalization off `
  --integration-rejection winsorized_sigma `
  --integration-weighting none `
  --flat-floor 0.05 `
  --resident-registration similarity_cuda_triangle `
  --resident-star-threshold 350 `
  --resident-star-max-candidates 48 `
  --resident-star-tolerance-px 3 `
  --resident-ncc-sample-stride 4 `
  --resident-warp-interpolation lanczos3 `
  --reference-frame-id LIGHT_H_0136 `
  --resident-output-maps audit `
  --resident-master-cache-dir C:\glass_runs\phase2_s2_gate486_master_raw_u16_ab_real\shared_master_cache
```

Runtime defaults intentionally omitted:

- no `--backend`
- no `--memory-mode`
- no `--resident-runtime-preset`
- no `--resident-integration-dispatch`

Resolved runtime:

- backend: `cuda`
- memory mode: `resident`
- default reason: `resident_cuda_default`
- runtime preset: `throughput-v1`
- resident integration dispatch: `stack`
- FITS read mode: guarded `auto`, effective native U16 GPU path

## Results

- Total GLASS run time: 19.786300399980973 s.
- WBPP speedup summary: 55.21704300016847x.
- Acceptance status: passed.
- Active frames: 193.
- Manifest frame counts: 200 light, 20 bias, 20 dark, 20 flat.
- Gate490 vs Gate489 master diff:
  - RMS: 0.0
  - p99 absolute diff: 0.0
  - max absolute diff: 0.0
- Gate490 vs WBPP scaled coverage-190 compare:
  - coverage fraction: 0.960532609259836
  - RMS diff: 0.0017794216505176163
  - p99 absolute diff: 0.00042621337808668863
  - max absolute diff: 0.5499989986419678

## Stage Timing Notes

From `resident_artifacts.json`:

- FITS native file read cumulative: 20.526960600000002 s.
- Read/decode worker cumulative: 20.65984609950101 s.
- Calibration store cumulative: 0.7164564514160155 s.
- H2D calibrate/store cumulative: 0.7334566997596994 s.
- Registration component accounted total: 2.118979298974204 s.
- Registration warp total: 0.5552684004069306 s.
- Moving catalog native total: 0.2610039 s.
- Moving catalog native sync: 0.2155821 s.
- Integration weighting: 0.001811699999962002 s.

The wall clock remains dominated by resident FITS materialization/read overlap,
with registration now a smaller secondary target.

## Artifacts

- Summary:
  `C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\summaries\gate490_real_post_cleanup_summary.json`
- GLASS vs Gate489 compare:
  `C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\compare\gate490_vs_gate489_master.json`
- GLASS vs WBPP compare:
  `C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\compare\gate490_vs_wbpp_scaled_coverage190.json`
- Speedup summary:
  `C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\speedup\gate490_vs_wbpp_speedup_with_compare.json`
- Pipeline contract:
  `C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\contracts\pipeline_contract.json`
- StackEngine contract:
  `C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\contracts\stack_engine_contract.json`
- Acceptance audit:
  `C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\acceptance\gate490_post_cleanup_acceptance_audit.json`
- HTML report:
  `C:\glass_runs\phase2_s2_gate490_post_cleanup_ab_real\reports\gate490_post_cleanup_report.html`

## Commands Run

```powershell
git diff --check
git status --short
git diff --stat
git add src/glass/cli.py tests/test_cli_smoke.py docs/algorithm_sources.md docs/phase2_algorithm_hardening.md runs/checkpoints/s2_gate_489_status.md
git commit -m "s2-gate-489: prove resident runtime default stack route"
git push origin main
.\.venv\Scripts\glass.exe run ...
.\.venv\Scripts\glass.exe compare ...
.\.venv\Scripts\glass.exe pipeline-contract --pixel-verify ...
.\.venv\Scripts\glass.exe stack-engine-contract --require-default-ready ...
.\.venv\Scripts\glass.exe speedup-summary ...
.\.venv\Scripts\glass.exe acceptance-audit ...
.\.venv\Scripts\glass.exe report ...
.\.venv\Scripts\python.exe -m pytest -q
```

## Tests

`.\.venv\Scripts\python.exe -m pytest -q`

Result:

`1127 passed in 41.66s`

## CUDA

CUDA was available.

`nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,compute_cap --format=csv,noheader`

Result:

`NVIDIA RTX PRO 6000 Blackwell Workstation Edition, 596.21, 97887 MiB, 824 MiB, 95776 MiB, 12.0`

## Known Limitations

- This gate did not modify algorithms; it is a real-data regression after
  cleanup.
- The preserved WBPP reference remains a black-box output and timing record.
- The master cache uses the existing selected calibration subset for the
  matching group while the manifest still contains 20 frames of each
  calibration type.

## Next Step

Return to substantive Phase 2 implementation:

1. FITS read/materialize overlap: reduce the remaining wall-clock dominated
   by native file read/materialization.
2. DQ/mask pipeline source-DQ closure: enable real-data source DQ input instead
   of the current no-source-DQ default path.

## Clean-Room Compliance

Compliant. This gate used GLASS artifacts, user-generated black-box
PixInsight/WBPP outputs, and public runtime metadata only. It did not inspect
or derive implementation details from official PixInsight/WBPP/PJSR source.
