# Resident Winsorized Benchmark

- Status: `passed`
- Passed: `True`
- Frames: `8`
- Shape: `16x16`

## Timing

| path | seconds |
| --- | ---: |
| CPU baseline | 0.014615500003856141 |
| CUDA fast approximation | 0.0008526000019628555 |
| CUDA hardened | 0.000185800003237091 |

## Differences

| comparison | RMS | max abs | p99 abs |
| --- | ---: | ---: | ---: |
| hardened master vs CPU | 5.781343294611998e-06 | 1.52587890625e-05 | 1.52587890625e-05 |
| fast master vs CPU | 0.566935986706338 | 5.23980712890625 | 4.125134658813474 |

## Failed Checks

- none
