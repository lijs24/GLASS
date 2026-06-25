# S2-Gate 693 Status: Component-Budget Mainline A/B

## Gate

S2-Gate 693.

## Completed Content

- Added stage-level component-ratio budgets to `glass phase2-mainline-ab`.
- Added the hard check `component_ratios_within_budget`.
- Added built-in Phase 2 budgets:
  - `light_read_upload_calibrate <= 1.50x`;
  - `resident_registration_warp <= 1.50x`;
  - `resident_local_normalization <= 1.50x`;
  - `resident_integration <= 1.25x`;
  - `output_write <= 2.00x`.
- Added CLI overrides:
  - `--max-component-ratio`;
  - repeatable `--component-ratio-budget COMPONENT=RATIO`.
- Added component-ratio rows, worst-component ratio, and failure counts to JSON
  and Markdown output.
- Extended `resident_runtime_compare` to include
  `resident_local_normalization` in timing deltas and Markdown tables.
- Added focused tests for passing component budgets and a component-regression
  failure that can fail even when the total elapsed ratio remains in budget.

## Real 200-Light Validation

- Baseline run:
  `C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\runs_20260627_034000\default_repeat`.
- Candidate run:
  `C:\glass_runs\phase2_s2_gate693_component_budget\runs_20260627_040000\component_budget_candidate`.
- Phase 2 mainline audit:
  `C:\glass_runs\phase2_s2_gate693_component_budget\gate693_phase2_mainline_audit.json`.
- Phase 2 mainline A/B:
  `C:\glass_runs\phase2_s2_gate693_component_budget\gate693_phase2_mainline_ab.json`.
- A/B Markdown:
  `C:\glass_runs\phase2_s2_gate693_component_budget\gate693_phase2_mainline_ab.md`.

Results:

- Phase 2 mainline audit: passed, failed checks `[]`.
- Phase 2 mainline A/B: passed, failed checks `[]`.
- Candidate active/masked frames: `193 / 7`.
- Candidate tracked map count: `6`.
- Hash mismatch count: `0`.
- Frame-index alignment status: `passed`.
- Component budget failures: `0`.
- Candidate total elapsed: `11.782868800219148 s`.
- Baseline-to-candidate elapsed ratio: `1.0237357465792638`.

Component ratios versus Gate692:

| Component | Baseline s | Candidate s | Ratio | Budget |
| --- | ---: | ---: | ---: | ---: |
| light read/upload/calibrate | `3.0809543000068516` | `3.1031843000091612` | `1.0072152968975425` | `1.50` |
| resident registration/warp | `0.2612904004054144` | `0.2666722999420017` | `1.0205973871532854` | `1.50` |
| resident local normalization | `0.3862151000648737` | `0.38270870002452284` | `0.9909211213135843` | `1.50` |
| resident integration | `3.266167899942957` | `3.2597308000549674` | `0.9980291583025778` | `1.25` |
| output write | `0.21337409992702305` | `0.224569599959068` | `1.0524688799431325` | `2.00` |

Largest candidate component:

- `resident_integration`: `3.2597308000549674 s`.

Next-largest component:

- `light_read_upload_calibrate`: `3.1031843000091612 s`.

## Commands Run

```powershell
.\.venv\Scripts\python.exe -m pip install -e .[dev,report]
.\.venv\Scripts\python.exe -m pytest -q tests/test_phase2_mainline_ab.py tests/test_resident_runtime_compare.py
.\.venv\Scripts\python.exe -m ruff check src/glass/report/phase2_mainline_ab.py src/glass/report/resident_runtime_compare.py src/glass/cli.py tests/test_phase2_mainline_ab.py
.\.venv\Scripts\glass.exe run --plan C:\glass_runs\phase2_s2_gate540_plan_spec_cache\runs_20260623_140314\processing_plan.json --out C:\glass_runs\phase2_s2_gate693_component_budget\runs_20260627_040000\component_budget_candidate --backend cuda --memory-mode resident --integration-weighting none --flat-floor 0.05 --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-output-maps audit --resident-master-cache-dir C:\glass_runs\phase2_s2_gate597_async_master_cache\resident_master_cache_async_final
.\.venv\Scripts\glass.exe phase2-mainline-ab --baseline-run C:\glass_runs\phase2_s2_gate692_probe_read_calibrate\runs_20260627_034000\default_repeat --candidate-run C:\glass_runs\phase2_s2_gate693_component_budget\runs_20260627_040000\component_budget_candidate --out C:\glass_runs\phase2_s2_gate693_component_budget\gate693_phase2_mainline_ab.json --markdown C:\glass_runs\phase2_s2_gate693_component_budget\gate693_phase2_mainline_ab.md --max-elapsed-ratio 1.15 --min-active-frame-count 190 --fail-on-failed
.\.venv\Scripts\glass.exe phase2-mainline-audit --run C:\glass_runs\phase2_s2_gate693_component_budget\runs_20260627_040000\component_budget_candidate --out C:\glass_runs\phase2_s2_gate693_component_budget\gate693_phase2_mainline_audit.json --markdown C:\glass_runs\phase2_s2_gate693_component_budget\gate693_phase2_mainline_audit.md --min-lights 200 --min-active-frames 190 --max-masked-frames 10 --fail-on-not-green
.\.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- Focused tests:
  `8 passed in 0.35 s`.
- Ruff:
  passed.
- Full pytest:
  `1437 passed in 66.75 s`.

## CUDA Status

- CUDA available: yes.
- Device: `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- Compute capability: `12.0`.
- VRAM: `97886 MiB`.
- Driver version: `596.21`.
- Native completion calibration: enabled in the real run.
- Native completion queue buffers: `32`.
- Native completion workers: `16`.

## Known Limitations

- This gate strengthens the real 200-light A/B acceptance surface. It does not
  change science pixels or optimize a resident CUDA kernel.
- Component budgets are intentionally permissive for I/O-heavy stages because
  external-disk variance is real on this workstation.
- The next performance gate should change implementation, not only add another
  evidence layer.

## Next Step

Return to implementation on the largest absolute costs:

- resident integration reducer, currently about `3.26 s`; or
- read/upload/calibration orchestration, currently about `3.10 s`.

Future candidates should use Gate693's A/B budget surface so total elapsed time,
component ratios, tracked maps, frame-index alignment, and active/masked frame
counts all remain green.

## Clean-Room Compliance

- No proprietary implementation source was read, copied, summarized, or
  reworked.
- The real input data was used read-only.
- The new logic is derived from GLASS-owned runtime timing and resident A/B
  artifacts.
- CUDA remains optional; CPU-only install and tests remain available.
