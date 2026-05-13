# GLASS PixInsight Launcher

`GLASS.js` is an optional clean-room PixInsight launcher for the external
`glass` command-line tool.

It is intentionally small:

- It does not implement image-processing algorithms.
- It does not import or modify official PixInsight preprocessing scripts.
- It writes outputs only to the run directory selected by the user.
- It can either run `glass audit` directly or write a `.cmd` file for review.

Suggested manual install:

1. Copy or reference this directory from a user-owned script location.
2. Open the script from PixInsight's Script Editor.
3. Fill in the GLASS executable, input root, and output run directory.
4. Prefer `Write command file` first so the exact external command can be
   reviewed before execution.

This launcher is optional. The supported and tested interface remains the
Python CLI.
