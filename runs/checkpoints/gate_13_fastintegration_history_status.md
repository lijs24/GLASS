# Gate 13 Checkpoint: WBPP FastIntegration History Diagnostic

Gate: 13

Completed content:
- Added `src/glass/report/wbpp_history.py` to parse user-generated XISF `PixInsight:ProcessingHistory`.
- Extracts the latest `FastIntegration` instance, parameters, `targets`, and `outputData` tables.
- Summarizes accepted and failed target rows from `totalPairMatches`/transform data.
- Added `glass blackbox-history --master ... --out ...`.
- Added tests for direct parsing, XISF property extraction, and CLI output.
- Ran the extractor on the M38 WBPP black-box master.

Commands run:
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_wbpp_history.py tests\test_cli_smoke.py`
- `.\.venv\Scripts\python.exe -m ruff check src\glass\report\wbpp_history.py src\glass\cli.py tests\test_wbpp_history.py`
- `.\.venv\Scripts\python.exe -m glass.cli blackbox-history --master "C:\glass_runs\final_m38_h_200\pixinsight_wbpp_blackbox\master\masterLight_BIN-1_9600x6422_EXPOSURE-600.00s_FILTER-H_mono_fastIntegration.xisf" --out "C:\glass_runs\final_m38_h_200\wbpp_fastintegration_history_cli.json"`
- `.\.venv\Scripts\python.exe -m pytest -q`

Test results:
- Targeted tests: 6 passed.
- Ruff targeted check: passed.
- Full pytest: 82 passed in 5.70s.

Real-data extraction result:
- Target rows: 200.
- Output rows: 200.
- Accepted rows: 193.
- Failed rows: 7.
- Failed target names: `LIGHT_H_0100_c.xisf`, `LIGHT_H_0153_c.xisf`, `LIGHT_H_0154_c.xisf`, `LIGHT_H_0155_c.xisf`, `LIGHT_H_0156_c.xisf`, `LIGHT_H_0157_c.xisf`, `LIGHT_H_0158_c.xisf`.
- Artifact: `C:\glass_runs\final_m38_h_200\wbpp_fastintegration_history_cli.json`.

CUDA availability:
- CUDA available: yes.
- Device: NVIDIA RTX PRO 6000 Blackwell Workstation Edition.
- Compute capability: 12.0.
- VRAM: 97886 MiB.

Known limitations:
- This parser is intentionally narrow: it extracts FastIntegration diagnostics needed for black-box comparison, not a general PixInsight history interpreter.
- It does not feed WBPP transforms or accepted-frame masks into GLASS automatically.
- It assumes the ProcessingHistory string is present within the first 32 MiB of the XISF file unless `--max-bytes` is increased.

Next step:
- Compare the extracted WBPP diagnostic table against GLASS's own star-registration table and improve GLASS's transform/warp implementation where differences are scientifically meaningful.

Clean-room compliance:
- Compliant. This reads only user-generated WBPP output metadata from the local run and records it as black-box diagnostics.
- No official WBPP/PJSR source was read, copied, summarized, or used as implementation input.
