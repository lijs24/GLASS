# Integration Model

Integration is designed as a tile-streaming accumulator. Initial CPU baseline
supports mean integration and sigma clipping on small synthetic stacks. Later
CUDA gates add weighted accumulators, coverage maps, and low/high rejection
maps without loading all registered lights into memory at once.

