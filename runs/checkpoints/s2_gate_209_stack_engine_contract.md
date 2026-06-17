# GLASS StackEngine Default Contract Audit

- Status: passed
- Run: `C:\glass_runs\phase2_s2_gate_209_native_artifact\contract_view`
- Scope: `all`
- Expected integration engine: `cuda_resident_stack`
- Resident calibration contract attached: `False`
- Resident result contract attached: `True`
- StackEngine adoption recommendation: `stack_engine_default_ready`
- Phase 2 StackEngine default gaps: `0`
- Default promotion ready: `True`

## Checks

- PASS: `calibration_artifact_exists` - {'path': 'C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view\\calibration_artifacts.json', 'exists': True, 'resident_calibration_contract_attached': False}
- PASS: `calibration_master_records_present` - {'actual': 3, 'required_min': 1}
- PASS: `calibration_masters_use_stack_engine` - {'master_count': 3, 'failed': []}
- PASS: `calibration_masters_science_auditable` - {'master_count': 3, 'failed': []}
- PASS: `integration_artifact_exists` - {'path': 'C:\\glass_runs\\phase2_s2_gate_209_native_artifact\\contract_view\\integration_results.json'}
- PASS: `integration_output_records_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_outputs_use:cuda_resident_stack` - {'output_count': 1, 'failed': []}

## StackEngine Adoption

- Target engine: `stack_engine_cpu`
- Surface count: `4`
- StackEngine surfaces: `0`
- Resident CUDA surfaces: `4`
- Contract-ready surfaces: `4`
- Gap count: `0`
- Recommendation: `stack_engine_default_ready`
- master_calibration:resident_bias_H_H_9600x6422_bias-G4ed2155578_dark-G59e41ba802_flat-G4f1de65e6a engine=cuda_resident_stack ready=True gap=False reason=
- master_calibration:resident_dark_H_H_9600x6422_bias-G4ed2155578_dark-G59e41ba802_flat-G4f1de65e6a engine=cuda_resident_stack ready=True gap=False reason=
- master_calibration:resident_flat_H_H_9600x6422_bias-G4ed2155578_dark-G59e41ba802_flat-G4f1de65e6a engine=cuda_resident_stack ready=True gap=False reason=
- integration:H engine=cuda_resident_stack ready=True gap=False reason=

## Default Promotion Guard

- Status: `ready`
- Ready: `True`
- Required scope: `all`
- Actual scope: `all`
- Blocker count: `0`
