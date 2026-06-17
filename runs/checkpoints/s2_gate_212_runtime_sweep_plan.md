# Candidate Runtime Sweep Plan

- Source candidate: `throughput_v1_preset_confirmation`
- Source recommendation: `eligible_but_needs_runtime_sweep`
- Variant count: `2`
- Recommendation: `execute_variants_sequentially_then_run_sweep_summary`

## Variants

| variant | purpose | changed options |
| --- | --- | --- |
| retry_settings_control | rerun the accepted candidate settings as a warm control | `{}` |
| prefetch12_workers7 | runtime confirmation sweep over resident prefetch depth and worker count | `{'--resident-prefetch-frames': 12, '--resident-prefetch-workers': 7}` |

## Sweep Command

```powershell
glass candidate-comparison-sweep --comparison C:\glass_runs\phase2_s2_gate_212_native_guardrails_sweep_plan\comparison\retry_settings_control_candidate_comparison.json --comparison C:\glass_runs\phase2_s2_gate_212_native_guardrails_sweep_plan\comparison\prefetch12_workers7_candidate_comparison.json --out C:\glass_runs\phase2_s2_gate_212_native_guardrails_sweep_plan\candidate_runtime_sweep.json --markdown C:\glass_runs\phase2_s2_gate_212_native_guardrails_sweep_plan\candidate_runtime_sweep.md --fail-on-no-passed
```

## Limitations

- This plan only changes runtime orchestration options; science options are inherited from the accepted candidate command.
- The plan writes commands but does not execute integration or image comparison.
- Generated commands are specific to the supplied benchmark paths and should be regenerated if artifacts move.
