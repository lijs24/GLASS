# GLASS StackEngine Default Contract Audit

- Status: passed
- Run: `runs\checkpoints\s2_gate_445_stackengine_work\cpu_synthetic\run`
- Scope: `all`
- Expected integration engine: `stack_engine_cpu`
- Resident calibration contract attached: `False`
- Resident result contract attached: `False`
- StackEngine adoption recommendation: `stack_engine_default_ready`
- Phase 2 StackEngine default gaps: `0`
- Strict native StackEngine default ready: `True`
- Default path status: `native_stack_engine_ready`
- Default promotion ready: `True`

## Checks

- PASS: `calibration_artifact_exists` - {'path': 'runs\\checkpoints\\s2_gate_445_stackengine_work\\cpu_synthetic\\run\\calibration_artifacts.json', 'exists': True, 'resident_calibration_contract_attached': False}
- PASS: `calibration_master_records_present` - {'actual': 3, 'required_min': 1}
- PASS: `calibration_masters_use_stack_engine` - {'master_count': 3, 'failed': []}
- PASS: `calibration_masters_science_auditable` - {'master_count': 3, 'failed': []}
- PASS: `integration_artifact_exists` - {'path': 'runs\\checkpoints\\s2_gate_445_stackengine_work\\cpu_synthetic\\run\\integration_results.json'}
- PASS: `integration_output_records_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_outputs_use:stack_engine_cpu` - {'output_count': 1, 'failed': []}

## StackEngine Adoption

- Target engine: `stack_engine_cpu`
- Surface count: `4`
- StackEngine surfaces: `4`
- Resident CUDA surfaces: `0`
- Contract-ready surfaces: `4`
- Gap count: `0`
- Recommendation: `stack_engine_default_ready`
- master_calibration:G409bfdf826 engine=stack_engine_cpu ready=True gap=False reason=
- master_calibration:G9e8d28c798 engine=stack_engine_cpu ready=True gap=False reason=
- master_calibration:Ga8f40c9e17 engine=stack_engine_cpu ready=True gap=False reason=
- integration:H engine=stack_engine_cpu ready=True gap=False reason=

## Default Path

- Status: `native_stack_engine_ready`
- Strict native ready: `True`
- Native StackEngine surfaces: `4`
- Resident CUDA contract-emulation surfaces: `0`
- Strict gap count: `0`
- master_calibration:G409bfdf826 role=native_stack_engine_default contract_ready=True strict_gap=False reason=
- master_calibration:G9e8d28c798 role=native_stack_engine_default contract_ready=True strict_gap=False reason=
- master_calibration:Ga8f40c9e17 role=native_stack_engine_default contract_ready=True strict_gap=False reason=
- integration:H role=native_stack_engine_default contract_ready=True strict_gap=False reason=

## Default Promotion Guard

- Status: `ready`
- Ready: `True`
- Required scope: `all`
- Actual scope: `all`
- Blocker count: `0`
