# GLASS Acceptance Audit

- Status: failed
- Benchmark contract: None
- Contract bundle: None
- Pipeline contract: failed
- StackEngine contract: None
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

- Status: failed
- Required by benchmark contract: False
- Pipeline contract path: runs\checkpoints\s2_gate_294_fixtures\acceptance\pipeline_legacy_master.json
- Pipeline contract audit type: pipeline_invariant_contract
- Pipeline contract passed: False
- Pipeline contract checks: 5
- Acceptance pipeline checks passed: 2
- Acceptance pipeline checks failed: 2
- Failed pipeline checks: ['pipeline_contract_passed', 'pipeline_contract_stack_engine_runtime_default']

### Rejection Sample Accounting

- Status: not_available
- Check passed: None
- Pixel verification enabled: False
- Accounting rows: 0
- Required rows: 0
- Verified rows: 0
- Failed rows: 0

### Integration Engine Policy

- Status: passed
- Check passed: True
- Non-resident outputs: 0
- Resident outputs: 1
- Failed rows: 0

### StackEngine Runtime Default Path

- Status: failed
- Check passed: False
- Master rows: 1
- Master StackEngine rows: 0
- Master resident rows: 0
- Legacy master rows: 1
- Integration outputs: 1
- Integration StackEngine defaults: 0
- Integration resident outputs: 1
- Explicit CUDA fast paths: 0
- Failed master rows: 1
- Failed integration rows: 0
- Runtime-default master mismatch bias_legacy: mode=legacy_streaming_accumulator status=failed failures=['master_stack_engine_not_enabled', 'legacy_master_stack_mode']

### Integration Sample Accounting Closure

- Status: not_available
- Check passed: None
- Output rows: 1
- Present rows: 0
- Required rows: 0
- Failed rows: 0

- PASS: pipeline_contract_present - {'path': 'runs\\checkpoints\\s2_gate_294_fixtures\\acceptance\\pipeline_legacy_master.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- FAIL: pipeline_contract_passed - {'status': 'failed', 'failed_checks': ['stack_engine_runtime_default_path']}
- PASS: pipeline_contract_integration_default_engine_policy - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- FAIL: pipeline_contract_stack_engine_runtime_default - {'status': 'failed', 'check_present': True, 'check_passed': False, 'master_count': 1, 'legacy_master_count': 1, 'integration_output_count': 1, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [{'contract_ok': True, 'failures': ['master_stack_engine_not_enabled', 'legacy_master_stack_mode'], 'name': 'bias_legacy', 'path_exists': True, 'stack_engine_enabled': False, 'status': 'failed', 'tile_stack_mode': 'legacy_streaming_accumulator', 'type': 'bias'}], 'failed_outputs': []}

## StackEngine Default Promotion Evidence

- Status: not_requested
- Required by benchmark contract: False
- StackEngine contract path: None
- StackEngine contract audit type: None
- StackEngine contract passed: None
- StackEngine contract scope: None
- Default promotion ready: None
- Default promotion status: None
- Default promotion gaps: None
- Default promotion blockers: None
- Adoption recommendation: None
- Acceptance StackEngine checks passed: 0
- Acceptance StackEngine checks failed: 0
- Failed StackEngine checks: []


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
- PASS: pipeline_contract_present - {'path': 'runs\\checkpoints\\s2_gate_294_fixtures\\acceptance\\pipeline_legacy_master.json', 'exists': True, 'audit_type': 'pipeline_invariant_contract'}
- FAIL: pipeline_contract_passed - {'status': 'failed', 'failed_checks': ['stack_engine_runtime_default_path']}
- PASS: pipeline_contract_integration_default_engine_policy - {'status': 'passed', 'check_present': True, 'check_passed': True, 'non_resident_count': 0, 'failed_count': 0, 'failed_items': []}
- FAIL: pipeline_contract_stack_engine_runtime_default - {'status': 'failed', 'check_present': True, 'check_passed': False, 'master_count': 1, 'legacy_master_count': 1, 'integration_output_count': 1, 'explicit_cuda_fast_path_count': 0, 'failed_masters': [{'contract_ok': True, 'failures': ['master_stack_engine_not_enabled', 'legacy_master_stack_mode'], 'name': 'bias_legacy', 'path_exists': True, 'stack_engine_enabled': False, 'status': 'failed', 'tile_stack_mode': 'legacy_streaming_accumulator', 'type': 'bias'}], 'failed_outputs': []}

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
