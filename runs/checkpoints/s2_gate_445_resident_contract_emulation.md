# GLASS StackEngine Default Contract Audit

- Status: passed
- Run: `runs\checkpoints\s2_gate_444_matrix_work\compatible_u16\run_default`
- Scope: `all`
- Expected integration engine: `cuda_resident_stack`
- Resident calibration contract attached: `True`
- Resident result contract attached: `True`
- StackEngine adoption recommendation: `stack_engine_default_ready`
- Phase 2 StackEngine default gaps: `0`
- Strict native StackEngine default ready: `False`
- Default path status: `resident_cuda_contract_emulation`
- Default promotion ready: `True`

## Checks

- PASS: `calibration_artifact_exists` - {'path': 'runs\\checkpoints\\s2_gate_444_matrix_work\\compatible_u16\\run_default\\calibration_artifacts.json', 'exists': True, 'resident_calibration_contract_attached': True}
- PASS: `calibration_master_records_present` - {'actual': 3, 'required_min': 1}
- PASS: `calibration_masters_use_stack_engine` - {'master_count': 3, 'failed': []}
- PASS: `calibration_masters_science_auditable` - {'master_count': 3, 'failed': []}
- PASS: `integration_artifact_exists` - {'path': 'runs\\checkpoints\\s2_gate_444_matrix_work\\compatible_u16\\run_default\\integration_results.json'}
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
- master_calibration:resident_bias_H_H_24x24_bias-Ga8f40c9e17_dark-G409bfdf826_flat-G9e8d28c798 engine=cuda_resident_stack ready=True gap=False reason=
- master_calibration:resident_dark_H_H_24x24_bias-Ga8f40c9e17_dark-G409bfdf826_flat-G9e8d28c798 engine=cuda_resident_stack ready=True gap=False reason=
- master_calibration:resident_flat_H_H_24x24_bias-Ga8f40c9e17_dark-G409bfdf826_flat-G9e8d28c798 engine=cuda_resident_stack ready=True gap=False reason=
- integration:H engine=cuda_resident_stack ready=True gap=False reason=

## Default Path

- Status: `resident_cuda_contract_emulation`
- Strict native ready: `False`
- Native StackEngine surfaces: `0`
- Resident CUDA contract-emulation surfaces: `4`
- Strict gap count: `4`
- master_calibration:resident_bias_H_H_24x24_bias-Ga8f40c9e17_dark-G409bfdf826_flat-G9e8d28c798 role=resident_cuda_contract_emulation contract_ready=True strict_gap=True reason=resident_cuda_contract_emulation
- master_calibration:resident_dark_H_H_24x24_bias-Ga8f40c9e17_dark-G409bfdf826_flat-G9e8d28c798 role=resident_cuda_contract_emulation contract_ready=True strict_gap=True reason=resident_cuda_contract_emulation
- master_calibration:resident_flat_H_H_24x24_bias-Ga8f40c9e17_dark-G409bfdf826_flat-G9e8d28c798 role=resident_cuda_contract_emulation contract_ready=True strict_gap=True reason=resident_cuda_contract_emulation
- integration:H role=resident_cuda_contract_emulation contract_ready=True strict_gap=True reason=resident_cuda_contract_emulation

## Default Promotion Guard

- Status: `ready`
- Ready: `True`
- Required scope: `all`
- Actual scope: `all`
- Blocker count: `0`
