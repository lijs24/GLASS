# S2-Gate 160 Status: Throughput Preset Confirmation and Contract Update

## Gate

S2-Gate 160: Throughput Preset Confirmation and Contract Update.

## Completed Content

- Ran the 200-light benchmark using `--resident-runtime-preset throughput-v1`
  instead of manually expanding the Gate158 runtime scheduling flags.
- Verified the preset applied the intended effective values in
  `resident_io_pipeline`.
- Generated reference compare, baseline compare, acceptance audit, and
  candidate-comparison artifacts.
- Extended benchmark contracts with `required_command_token_groups`, allowing
  equivalent command evidence such as:
  - `--resident-h2d-mode pinned_ring`
  - `--resident-runtime-preset throughput-v1`
- Updated `benchmarks/phase2_m38_h_200_contract.json` to accept the preset path
  and the measured star-grid column variants.
- Updated `docs/phase2_algorithm_hardening.md`.
- Updated `docs/algorithm_sources.md`.

## Commands Run

- `.\.venv\Scripts\glass.exe run --plan C:\gpwbpp_runs\final_m38_h_200\processing_plan.json --out C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --backend cuda --until-stage integration --memory-mode resident --resident-runtime-preset throughput-v1 ...`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_reference.html --glass-scale 8.764434957115609e-06 --glass-offset 0.0006274500691899127 --glass-coverage-map C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1\integration\resident_coverage_map_H.fits --min-coverage 190.0`
- `.\.venv\Scripts\glass.exe compare --glass C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1\integration\resident_master_H.fits --reference C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\integration\resident_master_H.fits --out C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_baseline.html --glass-coverage-map C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1\integration\resident_coverage_map_H.fits --min-coverage 190.0`
- `.\.venv\Scripts\glass.exe acceptance-audit --manifest C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200\manifest.json --glass-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --wbpp-result C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\wbpp_blackbox_result.json --compare-json C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_reference.json --out C:\glass_runs\phase2_s2_gate_160_preset_confirmation\acceptance\throughput_v1_acceptance.json --benchmark-contract benchmarks\phase2_m38_h_200_contract.json`
- `.\.venv\Scripts\glass.exe candidate-comparison --baseline-run C:\glass_runs\phase2_s2_gate_119_agreement_downweight_high\pf16_pw8_b8_s4_w2_callback_queue_rfqueued_catdet_agr0p8_agrs200 --candidate-run C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1 --candidate-id throughput_v1_preset_confirmation ...`
- `.\.venv\Scripts\python.exe -m pytest -q tests/test_acceptance_audit.py`
- `.\.venv\Scripts\ruff.exe check .`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\glass.exe doctor --allow-cpu-only --json runs\checkpoints\s2_gate_160_doctor.json`

## Test Results

- Acceptance audit focused file: `11 passed in 0.44s`.
- Ruff: `All checks passed!`
- Full test suite while an unrelated GPU workload was active:
  `272 passed, 127 skipped in 16.93s`.
- CUDA skips were expected under the busy policy:
  `CUDA tests skipped: GPU is busy (100% utilization, 52472/97887 MiB used)`.

Earlier in this gate, the preset confirmation acceptance audit failed only
because the benchmark contract required literal command tokens that the preset
intentionally replaces. After adding token groups and updating the contract, the
same run passed acceptance.

## Confirmation Result

- Acceptance status: `passed`
- Candidate-comparison status: `passed`
- Candidate recommendation: `eligible_but_needs_runtime_sweep`
- Candidate elapsed: `23.330858499999977 s`
- Speedup versus black-box reference: `46.82815250883293x`
- Candidate / historical GLASS baseline ratio: `1.3028856184518163`
- Weighted/integrated frames: 193
- Zero-weight frames: 7
- Reference RMS diff: `0.0014945534429799121`
- Reference RMS relative delta: `0.000614575672043593`
- Reference p99 delta: `-0.01041714662729686`

The preset applied the intended runtime values:

- `prefetch_frames=12`
- `prefetch_workers=7`
- `prefetch_refill_mode=queued`
- `h2d_mode=pinned_ring`
- `calibration_batch_requested_frames=8`
- `calibration_batch_requested_streams=4`
- `calibration_wave_requested_frames=2`
- `calibration_release_mode_effective=callback_queue`

Compared with the Gate158 top candidate, the slower runtime came mostly from
read/decode wait:

- Gate158 top `light_read_wait_wall`: `3.378438200000005 s`
- Gate160 preset `light_read_wait_wall`: `8.282256500000358 s`
- Gate158 top `light_read_worker_cumulative`: `35.43158810000102 s`
- Gate160 preset `light_read_worker_cumulative`: `72.21142359999953 s`

## Artifacts

- Run:
  `C:\glass_runs\phase2_s2_gate_160_preset_confirmation\throughput_v1`
- Reference compare:
  `C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_reference.json`
- Baseline compare:
  `C:\glass_runs\phase2_s2_gate_160_preset_confirmation\compare\throughput_v1_vs_baseline.json`
- Acceptance:
  `C:\glass_runs\phase2_s2_gate_160_preset_confirmation\acceptance\throughput_v1_acceptance.json`
- Candidate comparison:
  `C:\glass_runs\phase2_s2_gate_160_preset_confirmation\comparison\throughput_v1_candidate_comparison.json`
- Doctor:
  `runs/checkpoints/s2_gate_160_doctor.json`

## CUDA Status

- `glass doctor`: CUDA available.
- GPU: NVIDIA RTX PRO 6000 Blackwell Workstation Edition
- Compute capability: 12.0
- VRAM: 97886 MiB reported by GLASS doctor
- Driver: 596.21
- Windows package try order: `cuda13`, `cuda12`, `cuda11`, `cpu`

## Known Limitations

- The preset command path is confirmed, but this run was slower than the
  Gate158 top measured command due to higher read/decode wait.
- `throughput-v1` remains opt-in and is not promoted to the default.
- Full pytest in this checkpoint skipped CUDA tests because another workload
  occupied the GPU after the real Gate160 CUDA run had already completed.

## Next Step

S2-Gate 161 should diagnose I/O/cache variance for throughput preset runs:
repeat `throughput-v1` with a warmed cache and compare `light_read_wait_wall`,
worker cumulative decode time, and output-write timing before deciding whether
the preset is stable enough for documentation as the recommended 96GB-VRAM path.

## Clean-Room Compliance

Compliant. This gate used GLASS commands, GLASS artifacts, and user-generated
black-box reference outputs only. It did not read external implementation
source, did not modify input image directories, and did not change scientific
defaults.
