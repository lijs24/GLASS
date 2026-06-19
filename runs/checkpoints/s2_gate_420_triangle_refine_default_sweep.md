# Resident Registration Matrix Sweep

- Variant count: `4`
- Matrix passed count: `1`
- Parity passed count: `0`
- Best variant: `triangle_no_pixel_refine`
- Recommendation: `matrix_ready_but_image_parity_blocked`
- Next target: `focus next gate on warp, DQ, rejection, or integration sample accounting`

## Ranked Variants

| Variant | Matrix passed | Max delta px | Mean delta px | RMS diff | P99 abs | Rejected delta | Matrix recommendation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `triangle_no_pixel_refine` | True | 0.008781854250385976 | 0.0039021745376517335 | 0.0996942253107213 | 0.22672576904296893 | 117 | registration_matrices_ready |
| `triangle_gate417` | False | 0.18305392208191398 | 0.16714125666991966 | 2.568470708484397 | 2.059838104248047 | 1580 | fix_resident_transform_estimation |
| `triangle_fine03125` | False | 0.18305392208191398 | 0.16714125666991966 | 2.568470708484397 | 2.059838104248047 | 1580 | fix_resident_transform_estimation |
| `translation_ncc_step00625` | False | 0.18305392208191398 | 0.16734804795648386 | None | None | None | fix_resident_transform_estimation |
