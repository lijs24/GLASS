# Resident Registration Matrix Sweep

- Variant count: `4`
- Matrix passed count: `0`
- Parity passed count: `0`
- Best variant: `triangle_gate417`
- Recommendation: `subpixel_refinement_still_blocked`
- Next target: `change resident transform refinement metric/model before running larger benchmarks`

## Ranked Variants

| Variant | Matrix passed | Max delta px | Mean delta px | RMS diff | P99 abs | Rejected delta | Matrix recommendation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `triangle_gate417` | False | 0.18305392208191398 | 0.16714125666991966 | 2.568470708484397 | 2.059838104248047 | 1580 | fix_resident_transform_estimation |
| `triangle_fine03125` | False | 0.18305392208191398 | 0.16714125666991966 | 2.568470708484397 | 2.059838104248047 | 1580 | fix_resident_transform_estimation |
| `translation_ncc_step00625` | False | 0.18305392208191398 | 0.16734804795648386 | None | None | None | fix_resident_transform_estimation |
| `translation_ncc` | False | 0.2562184973123085 | 0.23488917697034084 | None | None | None | fix_resident_transform_estimation |
