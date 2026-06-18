# GLASS Acceptance Audit

- Status: failed
- Benchmark contract: s2_gate_347_controlled_conflict_contract
- Contract bundle: None
- Pipeline contract: None
- StackEngine contract: None
- Warp quality contract: None
- DQ provenance records: 0
- Frame accounting artifact: runs\checkpoints\s2_gate_347_controlled_conflict_run\frame_accounting.json
- Speedup vs WBPP: 10.0
- Frame counts: {'light': 1, 'bias': 1, 'dark': 1, 'flat': 1}
- Shape match: True
- RMS diff: 0.001
- abs diff p99: 0.002
- Coverage fraction: 1.0

## Checks

## Pipeline Contract Evidence

- Status: not_requested
- Required by benchmark contract: False
- Pipeline contract path: None
- Pipeline contract audit type: None
- Pipeline contract passed: None
- Pipeline contract checks: 0
- Acceptance pipeline checks passed: 0
- Acceptance pipeline checks failed: 0
- Failed pipeline checks: []

### Rejection Sample Accounting

- Status: not_requested
- Check passed: None
- Pixel verification enabled: False
- Accounting rows: 0
- Required rows: 0
- Verified rows: 0
- Failed rows: 0

### Integration Engine Policy

- Status: not_requested
- Check passed: None
- Non-resident outputs: 0
- Resident outputs: 0
- Failed rows: 0

### StackEngine Runtime Default Path

- Status: not_requested
- Check passed: None
- Master rows: 0
- Master StackEngine rows: 0
- Master resident rows: 0
- Legacy master rows: 0
- Integration outputs: 0
- Integration StackEngine defaults: 0
- Integration resident outputs: 0
- Explicit CUDA fast paths: 0
- Failed master rows: 0
- Failed integration rows: 0

### Integration Sample Accounting Closure

- Status: not_requested
- Check passed: None
- Output rows: 0
- Present rows: 0
- Required rows: 0
- Failed rows: 0


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


## Resident Registration Fast Path Evidence

- Status: not_requested
- Required by benchmark contract: False
- Source: resident_artifacts_json
- Path: runs\checkpoints\s2_gate_347_controlled_conflict_run\resident_artifacts.json
- Available: False
- Mode: None
- Descriptor fit batch: None
- Pixel refine batch: None
- Triangle warp batch: None
- Triangle warp batch frames: None
- Warp copy mode: None
- Checks passed: 0
- Checks failed: 0
- Failed checks: []


- PASS: minimum_light_frames - {'actual': 1, 'required': 1}
- PASS: minimum_bias_frames - {'actual': 1, 'required': 0}
- PASS: minimum_dark_frames - {'actual': 1, 'required': 0}
- PASS: minimum_flat_frames - {'actual': 1, 'required': 0}
- PASS: minimum_active_frames - {'actual': 1, 'required': 1}
- PASS: minimum_speedup - {'actual': 10.0, 'required': 2.0}
- PASS: shape_match - {'actual': True, 'required': True}
- PASS: minimum_coverage_fraction - {'actual': 1.0, 'required': 0.95}
- PASS: maximum_rms_diff - {'actual': 0.001, 'required_max': 0.01}
- PASS: maximum_abs_diff_p99 - {'actual': 0.002, 'required_max': 0.01}
- PASS: contract_minimum_light_frames - {'actual': 1, 'required': 1}
- PASS: contract_minimum_bias_frames - {'actual': 1, 'required': 0}
- PASS: contract_minimum_dark_frames - {'actual': 1, 'required': 0}
- PASS: contract_minimum_flat_frames - {'actual': 1, 'required': 0}
- PASS: contract_minimum_active_light_frames - {'actual': 1, 'required': 1}
- PASS: contract_minimum_speedup_vs_reference - {'actual': 10.0, 'required': 2.0}
- PASS: contract_max_rms_diff - {'actual': 0.001, 'required_max': 0.01}
- PASS: contract_max_abs_diff_p99 - {'actual': 0.002, 'required_max': 0.01}
- PASS: contract_min_coverage_fraction - {'actual': 1.0, 'required': 0.95}
- PASS: contract_frame_accounting_present - {'path': 'runs\\checkpoints\\s2_gate_347_controlled_conflict_run\\frame_accounting.json', 'exists': True}
- PASS: contract_frame_accounting_input_light_frames - {'actual': 1, 'required': 1}
- PASS: contract_frame_accounting_integrated_frames - {'actual': 0, 'required': 0}
- PASS: contract_frame_accounting_zero_weight_frames - {'actual': 0, 'required': 0}
- PASS: contract_frame_accounting_registration_accepted_frames - {'actual': 0, 'required': 0}
- PASS: contract_frame_accounting_final_status:integration_conflict - {'actual': 1, 'calculated_from_rows': 1, 'required': 1}
- FAIL: contract_frame_accounting_no_integration_conflicts - {'conflict_count': 1, 'conflicts': [{'frame_id': 'conflict', 'final_status': 'integration_conflict', 'integration_weight': 1.0, 'registration_status': 'quality_rejected', 'warp_status': 'skipped', 'local_norm_status': 'not_run', 'conflicts': [{'reason': 'positive integration weight for quality-rejected frame', 'stage': 'quality', 'status': 'rejected'}, {'reason': 'positive integration weight for non-accepted registration frame', 'stage': 'registration', 'status': 'quality_rejected'}, {'reason': 'positive integration weight for non-warped frame', 'stage': 'warp', 'status': 'skipped'}]}]}

## Frame Accounting

- Exists: True
- Input lights: 1
- Integrated frames: 0
- Zero-weight frames: 0
- Final status counts: {'integration_conflict': 1}
- Exception summary: {'count': 1, 'final_status_counts': {'integration_conflict': 1}, 'primary_stage_counts': {'quality': 1}}
- Integration weight counts: {'total': 1, 'positive': 1, 'zero': 0, 'invalid': 0}
- Registration counts: {'total': 1, 'accepted': 0, 'zero_weight_statuses': 1, 'status_counts': {'quality_rejected': 1}}
- Exception frame: conflict status=integration_conflict stage=quality reason=positive integration weight for quality-rejected frame

## Resident Registration Fast Path

- Exists: True
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
