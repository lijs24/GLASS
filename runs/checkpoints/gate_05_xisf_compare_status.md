# Gate 05 XISF Compare Status

## Gate

Direct comparison against PixInsight/WBPP black-box XISF master outputs.

## Completed

- Added uncompressed attachment-backed XISF image reading for Float32/Float64
  and common integer sample formats.
- Extended compare support so `gpwbpp compare` can compare FITS to XISF.
- Added raw difference metrics, absolute-difference percentiles, linear fit, and
  robust linear fit metrics.
- Added tests for XISF Float32 reading and FITS-vs-XISF comparison.
- Compared the current GPWBPP resident formal master against the WBPP
  `masterLight` XISF output.

## Commands

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_xisf_io.py
.venv\Scripts\python.exe -m gpwbpp.cli compare --gpwbpp C:\gpwbpp_runs\final_m38_h_200\gpwbpp_resident_formal_run\integration\resident_master_H.fits --reference C:\gpwbpp_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf --out C:\gpwbpp_runs\final_m38_h_200\current_resident_vs_wbpp_compare.html --gpwbpp-time-seconds 58.9810051000095 --reference-time-seconds 1092.541 --gpwbpp-label GPWBPP-resident-current --reference-label PixInsight-WBPP-fastIntegration
.venv\Scripts\python.exe -m pytest -q
```

## Test Results

- XISF tests: 2 passed in 0.04 s.
- Full test suite: 69 passed in 5.61 s.

## Comparison Result

- Shape match: yes, `9600 x 6422`.
- Speedup for the current resident gate path: 18.52x versus WBPP black-box total.
- Result agreement: not yet acceptable for final validation.
- Raw RMS is dominated by extreme GPWBPP pixels caused by invalid/near-zero flat
  regions.
- Robust-fit central pixels show much smaller differences, but full-image
  agreement fails until flat masking/coverage, rejection, registration, and crop
  semantics are implemented.

## Artifacts

- `C:\gpwbpp_runs\final_m38_h_200\current_resident_vs_wbpp_compare.json`
- `C:\gpwbpp_runs\final_m38_h_200\current_resident_vs_wbpp_compare.html`

## Known Limitations

- XISF reader currently supports uncompressed attachment-backed image blocks.
- Compressed XISF blocks and multi-image containers fail explicitly.
- This comparison gate proves that the current resident output is fast but not
  yet scientifically equivalent to WBPP output.

## Next Step

Implement flat validity masks, coverage maps, and WBPP-like crop/rejection
semantics before claiming final output consistency.

## Clean Room

Compliant. WBPP output was consumed as a black-box artifact. No official
WBPP/PJSR source was read or copied.
