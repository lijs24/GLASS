# Known Limitations

Current Gate 0-2 code is intentionally modest:

- CUDA extension files are present as skeletons only until Gate 3.
- XISF parsing is provisional and limited to the XML prefix.
- CPU registration currently estimates only simple translation from ordered
  star lists.
- Local normalization is a global helper placeholder until Gate 10.
- Integration is CPU mean/sigma clipping on in-memory small stacks until the
  streaming gates are implemented.
- HTML reports include required sections but many stage-specific tables remain
  pending until their gates produce artifacts.
- No equivalence with PixInsight/WBPP is claimed.

These limitations are capability flags, not hidden behavior. Later gates must
replace placeholders with tested implementations and checkpoint their status.

