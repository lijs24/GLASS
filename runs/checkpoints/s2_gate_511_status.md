# S2-Gate 511 Status: Throughput v3 I/O Prefetch Retune

Gate: S2-Gate 511

## Result

Passed.

This gate makes a concrete Phase 2 resident runtime default change: the
`throughput-v3-io` preset now uses a deeper I/O prefetch queue, moving from
`32` frames / `12` workers to `48` frames / `16` workers. The calibration batch,
stream, and wave settings remain `16/4/4` because a same-cache probe showed
batch-24 was slower.

## Completed

- Updated `src/glass/cli.py` resident `throughput-v3-io` preset:
  - `resident_prefetch_frames=48`;
  - `resident_prefetch_workers=16`;
  - calibration batch/wave unchanged at `16/4/4`.
- Updated `src/glass/report/benchmark_contract.py` so acceptance artifact
  matching expects the new default preset signature.
- Updated CLI and acceptance-audit tests.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands

- `python -m ruff check src\glass\cli.py src\glass\report\benchmark_contract.py tests\test_cli_smoke.py tests\test_acceptance_audit.py`
- `python -m pytest -q tests\test_cli_smoke.py::test_resident_runtime_preset_throughput_v3_io_applies_probe_values tests\test_cli_smoke.py::test_resident_runtime_preset_defaults_to_throughput_v3_io tests\test_acceptance_audit.py::test_acceptance_audit_accepts_io_runtime_preset_from_artifact`
- Probe runs under:
  `C:\glass_runs\phase2_s2_gate511_probe_io_registration\runs_20260623_064702`
- Default-path run:
  `glass run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --backend cuda --memory-mode resident --until-stage integration --local-normalization off --integration-rejection winsorized_sigma --integration-weighting none --flat-floor 0.05 --resident-registration similarity_cuda_triangle --resident-star-threshold 350 --resident-star-max-candidates 48 --resident-star-tolerance-px 3 --resident-ncc-sample-stride 4 --resident-warp-interpolation lanczos3 --reference-frame-id LIGHT_H_0136 --resident-output-maps minimal --resident-master-cache-dir C:\glass_runs\phase2_s2_gate510_resident_calibration_contract_ab_real\runs_20260623_063856\shared_master_cache --out C:\glass_runs\phase2_s2_gate511_v3_io_prefetch48_default_ab_real\runs_20260623_064914\default_prefetch48`
- `glass stack-engine-contract --run C:\glass_runs\phase2_s2_gate511_v3_io_prefetch48_default_ab_real\runs_20260623_064914\default_prefetch48 --scope all --expected-integration-engine cuda_resident_stack --require-default-ready --out C:\glass_runs\phase2_s2_gate511_v3_io_prefetch48_default_ab_real\runs_20260623_064914\default_stack_engine_contract.json`
- `python -m ruff check src tests`
- `python -m pytest -q`
- `glass doctor`

## Test Result

- Focused tests: `3 passed`.
- Full test suite: `1154 passed in 41.76 s`.
- Ruff: passed.

## CUDA

- CUDA available: yes.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.
- Driver: 596.21.

## Real 200-Light Probe

Probe root:

`C:\glass_runs\phase2_s2_gate511_probe_io_registration\runs_20260623_064702`

Results:

- `prefetch48_workers16`: total `6.59302689996548 s`, read wait
  `0.5751616001361981 s`.
- `calbatch24_streams4`: total `6.7247856999747455 s`, read wait
  `1.1384011003538035 s`.
- `prefetch48_calbatch24`: total `6.577672699990217 s`, read wait
  `0.601900500478223 s`.
- `prefetch64_workers16`: total `6.802674999984447 s`, read wait
  `0.5411046000663191 s`.

Decision:

- Promote `48/16` prefetch.
- Do not promote `64/16` prefetch because wall time regressed.
- Do not promote calibration batch 24 because it regressed.

## Real 200-Light Default Validation

Run root:

`C:\glass_runs\phase2_s2_gate511_v3_io_prefetch48_default_ab_real\runs_20260623_064914`

Results:

- Default run: `6.5765664000064135 s`.
- Gate510 repeat baseline: `6.658429500006605 s`.
- Delta vs Gate510: `-0.08186310000019148 s`.
- Speedup vs Gate510: `1.0124476961108628x`.
- WBPP black-box reference time: `1092.541 s`.
- Speedup vs WBPP: `166.1263543235775x`.
- Read wait: `0.5706713998806663 s`.
- Gate510 repeat read wait: `0.9934065002016723 s`.
- Read wait delta: `-0.42273510032100603 s`.
- Applied runtime preset:
  - `resident_runtime_preset=throughput-v3-io`;
  - `resident_prefetch_frames=48`;
  - `resident_prefetch_workers=16`;
  - `resident_calibration_batch_frames=16`;
  - `resident_calibration_streams=4`;
  - `resident_calibration_wave_frames=4`.
- Gate511 default master vs Gate510 repeat: bitwise equal, RMS `0.0`, max abs
  `0.0`, finite pixels `61651200`.
- StackEngine contract audit: passed with `--require-default-ready`.

WBPP comparison:

- The Gate511 default master is bitwise identical to Gate510 and Gate509 repeat
  masters, so the existing Gate509 WBPP metrics remain valid.
- Inherited WBPP compare source:
  `C:\glass_runs\phase2_s2_gate509_lanczos_unclamped_specialized_ab_real\runs_20260623_062926\compare_vs_wbpp_fastintegration_scaled_coverage190.json`
- RMS diff: `0.0017794216505176163`.
- P99 absolute diff: `0.00042621337808668863`.

## Artifacts

- `C:\glass_runs\phase2_s2_gate511_v3_io_prefetch48_default_ab_real\runs_20260623_064914\gate511_default_prefetch48_summary.json`
- `C:\glass_runs\phase2_s2_gate511_v3_io_prefetch48_default_ab_real\runs_20260623_064914\gate511_wbpp_speedup_summary.json`
- `C:\glass_runs\phase2_s2_gate511_v3_io_prefetch48_default_ab_real\runs_20260623_064914\gate511_wbpp_speedup_summary.md`
- `C:\glass_runs\phase2_s2_gate511_v3_io_prefetch48_default_ab_real\runs_20260623_064914\default_stack_engine_contract.json`

## Known Limitations

- The speed win is modest because registration/warp remains the largest
  resident component.
- The larger `64/16` prefetch probe reduced read wait but increased total wall
  time, so it remains rejected for this default.
- The WBPP image-difference metrics were not recomputed from the original WBPP
  image in this gate; they are inherited after proving bitwise equality to the
  already-compared Gate509 master.
- Strict native `stack_engine_cpu` default is still not claimed for resident
  CUDA surfaces.

## Clean-Room Compliance

Compliant. This gate used GLASS timing artifacts, GLASS code, GLASS tests, and
user-generated benchmark comparison data. No official PixInsight/WBPP/PJSR
source was read or used.

## Next Step

S2-Gate 512 should target resident registration/warp batching and synchronization
reduction, because Gate511 shows the I/O wait is now smaller than the
registration/warp component on the warm-cache 200-light benchmark.
