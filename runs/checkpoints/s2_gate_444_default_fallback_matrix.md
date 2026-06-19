# Resident FITS Default Compatibility Matrix

- Status: `passed`
- Cases: `4`
- Failed cases: `none`

| Case | Passed | Resident | Source | Requested | Effective | Backends | Raw selected | Fallback reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| default_compatible_u16 | yes | yes | resident_cuda_guarded_auto_default | auto | native_u16_gpu | native_u16be_raw=2 | True | {} |
| default_incompatible_float32 | yes | yes | resident_cuda_guarded_auto_default | auto | auto | fast_simple=2 | False | bitpix_not_16:-32=2 |
| explicit_astropy_escape_hatch | yes | yes | explicit | astropy | astropy | astropy_scaled_memmap=2 | False | {} |
| cpu_tile_unaffected | yes | no | unused_non_resident | None | None | {} | None | {} |
