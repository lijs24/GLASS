# GLASS StackEngine Default Contract Audit

- Status: passed
- Run: `C:\glass_runs\phase2_s2_gate_32_200\resident_artifact_paths_20260531`
- Scope: `integration`
- Expected integration engine: `cuda_resident_stack`

## Checks

- PASS: `integration_artifact_exists` - {'path': 'C:\\glass_runs\\phase2_s2_gate_32_200\\resident_artifact_paths_20260531\\integration_results.json'}
- PASS: `integration_output_records_present` - {'actual': 1, 'required_min': 1}
- PASS: `integration_outputs_use:cuda_resident_stack` - {'output_count': 1, 'failed': []}
