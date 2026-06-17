# GLASS Acceptance Audit

- Status: passed
- Benchmark contract: None
- Contract bundle: passed
- Pipeline contract: passed
- StackEngine contract: passed
- DQ provenance records: 1
- Frame accounting artifact: C:\glass_runs\phase2_s2_gate_198_guardrails_contract_bundle\run\frame_accounting.json
- Speedup vs WBPP: 25.484992143062193
- Frame counts: {'light': 4, 'bias': 3, 'dark': 3, 'flat': 3}
- Shape match: True
- RMS diff: 0.001
- abs diff p99: 0.002
- Coverage fraction: 1

## Checks

## Pipeline Contract Evidence

- Status: passed
- Required by benchmark contract: False
- Pipeline contract path: C:\glass_runs\phase2_s2_gate_198_guardrails_contract_bundle\guardrails\pipeline_contract.json
- Pipeline contract audit type: pipeline_invariant_contract
- Pipeline contract passed: True
- Pipeline contract checks: 12
- Acceptance pipeline checks passed: 2
- Acceptance pipeline checks failed: 0
- Failed pipeline checks: []

- PASS: pipeline_contract_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_198_guardrails_contract_bundle\\guardrails\\pipeline_contract.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_checks': []}

## StackEngine Default Promotion Evidence

- Status: passed
- Required by benchmark contract: False
- StackEngine contract path: C:\glass_runs\phase2_s2_gate_198_guardrails_contract_bundle\guardrails\stack_engine_contract.json
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

- PASS: stack_engine_contract_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_198_guardrails_contract_bundle\\guardrails\\stack_engine_contract.json', 'exists': True, 'audit_type': 'stack_engine_default_contract'}
- PASS: stack_engine_contract_passed - {'status': 'passed', 'failed_checks': []}

- PASS: minimum_light_frames - {'actual': 4, 'required': 1}
- PASS: minimum_bias_frames - {'actual': 3, 'required': 1}
- PASS: minimum_dark_frames - {'actual': 3, 'required': 1}
- PASS: minimum_flat_frames - {'actual': 3, 'required': 1}
- PASS: minimum_active_frames - {'actual': 2, 'required': 2}
- PASS: minimum_speedup - {'actual': 25.484992143062193, 'required': 2.0}
- PASS: shape_match - {'actual': True, 'required': True}
- PASS: minimum_coverage_fraction - {'actual': 1.0, 'required': 0.95}
- PASS: maximum_rms_diff - {'actual': 0.001, 'required_max': 0.01}
- PASS: maximum_abs_diff_p99 - {'actual': 0.002, 'required_max': 0.01}
- PASS: contract_bundle_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_198_guardrails_contract_bundle\\guardrails\\acceptance_contract_bundle.json', 'exists': True}
- PASS: contract_bundle_type - {'path': 'C:\\glass_runs\\phase2_s2_gate_198_guardrails_contract_bundle\\guardrails\\acceptance_contract_bundle.json', 'artifact_type': 'glass_acceptance_contract_bundle', 'required': 'glass_acceptance_contract_bundle'}
- PASS: pipeline_contract_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_198_guardrails_contract_bundle\\guardrails\\pipeline_contract.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- PASS: pipeline_contract_passed - {'status': 'passed', 'failed_checks': []}
- PASS: stack_engine_contract_present - {'path': 'C:\\glass_runs\\phase2_s2_gate_198_guardrails_contract_bundle\\guardrails\\stack_engine_contract.json', 'exists': True, 'audit_type': 'stack_engine_default_contract'}
- PASS: stack_engine_contract_passed - {'status': 'passed', 'failed_checks': []}

## DQ Provenance

- integration_results.json[0] schema=stack_engine_dq_provenance engine=stack_engine_cpu stage=integration item=H dq_map_exists=True legacy_normalized=False pixel_verification=None coverage_verification=None

## Frame Accounting

- Exists: True
- Input lights: 4
- Integrated frames: 2
- Zero-weight frames: 0
- Final status counts: {'integrated': 2, 'quality_rejected': 2}
- Exception summary: {'count': 2, 'final_status_counts': {'quality_rejected': 2}, 'primary_stage_counts': {'quality': 2}}
- Integration weight counts: {'total': 2, 'positive': 2, 'zero': 0, 'invalid': 0}
- Registration counts: {'total': 4, 'accepted': 2, 'zero_weight_statuses': 2, 'status_counts': {'quality_rejected': 2, 'ok': 1, 'reference': 1}}
- Exception frame: F000010 status=quality_rejected stage=quality reason=star_count 7 below min_stars=8
- Exception frame: F000013 status=quality_rejected stage=quality reason=star_count 7 below min_stars=8

## Clean-room

- Acceptance audit consumes GLASS artifacts and user-generated PixInsight/WBPP black-box timing/output metadata only.
