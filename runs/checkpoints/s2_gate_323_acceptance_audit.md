# GLASS Acceptance Audit

- Status: passed
- Benchmark contract: None
- Contract bundle: passed
- Pipeline contract: passed
- StackEngine contract: passed
- Warp quality contract: passed
- DQ provenance records: 0
- Frame accounting artifact: runs\checkpoints\s2_gate_294_fixtures\acceptance\gp\frame_accounting.json
- Speedup vs WBPP: 10.0
- Frame counts: {'light': 200, 'bias': 20, 'dark': 20, 'flat': 20}
- Shape match: True
- RMS diff: 0.001
- abs diff p99: 0.002
- Coverage fraction: 0.97

## Checks

## Pipeline Contract Evidence

- Status: passed
- Required by benchmark contract: False
- Pipeline contract path: runs\checkpoints\s2_gate_321_guardrails\pipeline_contract.json
- Pipeline contract audit type: pipeline_invariant_contract
- Pipeline contract passed: True
- Pipeline contract checks: 22
- Acceptance pipeline checks passed: 4
- Acceptance pipeline checks failed: 0
- Failed pipeline checks: []

### Rejection Sample Accounting

- Status: passed
- Check passed: True
- Pixel verification enabled: True
- Accounting rows: 1
- Required rows: 0
- Verified rows: 1
- Failed rows: 0

### Integration Engine Policy

- Status: passed
- Check passed: True
- Non-resident outputs: 1
- Resident outputs: 0
- Failed rows: 0

### StackEngine Runtime Default Path

- Status: passed
- Check passed: True
- Master rows: 3
- Master StackEngine rows: 3
- Master resident rows: 0
- Legacy master rows: 0
- Integration outputs: 1
- Integration StackEngine defaults: 1
- Integration resident outputs: 0
- Explicit CUDA fast paths: 0
- Failed master rows: 0
- Failed integration rows: 0

### Integration Sample Accounting Closure

- Status: passed
- Check passed: True
- Output rows: 1
- Present rows: 1
- Required rows: 1
- Failed rows: 0

- PASS: pipeline_contract_present - {'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\pipeline_contract.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: pipeline_contract_integration_default_engine_policy - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 1, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_contract_stack_engine_runtime_default - {'status': 'passed', 'check_present': True, 'check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'integration_output_count': 1, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [], 'failed_outputs': []}

## StackEngine Default Promotion Evidence

- Status: passed
- Required by benchmark contract: False
- StackEngine contract path: runs\checkpoints\s2_gate_321_guardrails\stack_engine_contract.json
- StackEngine contract audit type: stack_engine_default_contract
- StackEngine contract passed: True
- StackEngine contract scope: all
- Default promotion ready: True
- Default promotion status: ready
- Default promotion gaps: 0
- Default promotion blockers: 0
- Adoption recommendation: stack_engine_default_ready
- Acceptance StackEngine checks passed: 2
- Acceptance StackEngine checks failed: 0
- Failed StackEngine checks: []

- PASS: stack_engine_contract_present - {'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\stack_engine_contract.json', 'exists': True, 'audit_type': 'stack_engine_default_contract'}
- PASS: stack_engine_contract_passed - {'status': 'passed', 'failed_checks': []}

## Contract Bundle Schema

- Status: passed
- Schema version: 1 (required 1)
- Purpose: acceptance_audit_contract_inputs (required acceptance_audit_contract_inputs)
- Artifact keys: ['guardrails_summary', 'local_norm_contract', 'local_norm_contract_markdown', 'pipeline_contract', 'pipeline_contract_markdown', 'registration_quality_contract', 'registration_quality_contract_markdown', 'report', 'resident_calibration_contract', 'resident_result_contract', 'stack_engine_contract', 'stack_engine_contract_markdown', 'warp_quality_contract', 'warp_quality_contract_markdown']
- Missing artifacts: []
- Argument map keys: ['pipeline_contract_json', 'stack_engine_contract_json']
- Missing argument map keys: []

## Native Guardrails Bundle Provenance

- Status: present
- Bundle status: passed
- Guardrails summary: runs\checkpoints\s2_gate_321_guardrails\guardrails_summary.json
- Resident result contract source: missing
- Resident result contract run default: False
- Resident result contract: None
- Resident native calibration artifact: False
- Resident calibration master count: 3
- Resident calibrated light count: 0

## Warp Quality Contract

- Status: passed
- Passed: True
- Type: warp_quality_contract
- Checks: 9
- Outputs: 1
- Path: runs\checkpoints\s2_gate_321_guardrails\warp_quality_contract.json

- PASS: minimum_light_frames - {'actual': 200, 'required': 200}
- PASS: minimum_bias_frames - {'actual': 20, 'required': 20}
- PASS: minimum_dark_frames - {'actual': 20, 'required': 20}
- PASS: minimum_flat_frames - {'actual': 20, 'required': 20}
- PASS: minimum_active_frames - {'actual': 193, 'required': 190}
- PASS: minimum_speedup - {'actual': 10.0, 'required': 2.0}
- PASS: shape_match - {'actual': True, 'required': True}
- PASS: minimum_coverage_fraction - {'actual': 0.97, 'required': 0.95}
- PASS: maximum_rms_diff - {'actual': 0.001, 'required_max': 0.01}
- PASS: maximum_abs_diff_p99 - {'actual': 0.002, 'required_max': 0.01}
- PASS: contract_bundle_present - {'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\acceptance_contract_bundle.json', 'exists': True}
- PASS: contract_bundle_type - {'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\acceptance_contract_bundle.json', 'artifact_type': 'glass_acceptance_contract_bundle', 'required': 'glass_acceptance_contract_bundle'}
- PASS: contract_bundle_schema_version - {'actual': 1, 'required': 1}
- PASS: contract_bundle_purpose - {'actual': 'acceptance_audit_contract_inputs', 'required': 'acceptance_audit_contract_inputs'}
- PASS: contract_bundle_required_artifacts - {'required': ['guardrails_summary', 'pipeline_contract', 'stack_engine_contract'], 'missing': [], 'actual': ['guardrails_summary', 'local_norm_contract', 'local_norm_contract_markdown', 'pipeline_contract', 'pipeline_contract_markdown', 'registration_quality_contract', 'registration_quality_contract_markdown', 'report', 'resident_calibration_contract', 'resident_result_contract', 'stack_engine_contract', 'stack_engine_contract_markdown', 'warp_quality_contract', 'warp_quality_contract_markdown']}
- PASS: contract_bundle_argument_map - {'required': ['pipeline_contract_json', 'stack_engine_contract_json'], 'missing': [], 'actual': ['pipeline_contract_json', 'stack_engine_contract_json']}
- PASS: warp_quality_contract_present - {'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\warp_quality_contract.json', 'exists': True}
- PASS: warp_quality_contract_type - {'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\warp_quality_contract.json', 'artifact_type': 'warp_quality_contract', 'required': 'warp_quality_contract'}
- PASS: warp_quality_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: pipeline_contract_present - {'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\pipeline_contract.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: pipeline_contract_integration_default_engine_policy - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 1, 'failed_count': 0, 'failed_items': []}
- PASS: pipeline_contract_stack_engine_runtime_default - {'status': 'passed', 'check_present': True, 'check_passed': True, 'master_count': 3, 'legacy_master_count': 0, 'integration_output_count': 1, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [], 'failed_outputs': []}
- PASS: stack_engine_contract_present - {'path': 'runs\\checkpoints\\s2_gate_321_guardrails\\stack_engine_contract.json', 'exists': True, 'audit_type': 'stack_engine_default_contract'}
- PASS: stack_engine_contract_passed - {'status': 'passed', 'failed_checks': []}

## Frame Accounting

- Exists: False
- Input lights: None
- Integrated frames: None
- Zero-weight frames: None
- Final status counts: None
- Exception summary: {}
- Integration weight counts: {'total': 200, 'positive': 193, 'zero': 7, 'invalid': 0}
- Registration counts: {'total': 0, 'accepted': 0, 'zero_weight_statuses': 0, 'status_counts': {}}

## Resident Registration Fast Path

- Exists: False
- Available: False
- Mode: None
- Descriptor fit batch: None
- Descriptor fit batch mode: None
- Descriptor device reuse: reference=None moving=None output=None
- Pixel refine batch: None
- Pixel refine metric mode: None
- Triangle warp batch: None
- Triangle warp batch mode: None
- Warp copy mode: None
- I/O pipeline warp copy mode: None
- Warp scratch bytes: None
- Component seconds: {}

## Clean-room

- Acceptance audit consumes GLASS artifacts and user-generated PixInsight/WBPP black-box timing/output metadata only.
