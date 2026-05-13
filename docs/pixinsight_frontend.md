# Optional PixInsight Front-end

Gate 14 is represented by `pixinsight/GLASS.js`, a clean-room launcher for the
external GLASS CLI.

The front-end boundary is strict:

- It calls `glass audit` as an external executable.
- It does not copy, import, read, or modify official PixInsight preprocessing
  scripts.
- It does not implement scientific image-processing kernels.
- It does not write to the input data directory.

The launcher exposes only a small set of GLASS CLI options:

- input root;
- output run directory;
- backend;
- memory mode;
- local normalization;
- integration weighting;
- integration rejection;
- resident registration;
- resident warp interpolation.

The launcher also has a command-file mode. That mode is preferred for
reproducible benchmark runs because the generated `.cmd` file can be inspected
before execution and archived with the run artifacts.

Current limitation: this front-end is a clean-room optional convenience layer.
The tested and supported automation entry point remains `glass` on the command
line.
