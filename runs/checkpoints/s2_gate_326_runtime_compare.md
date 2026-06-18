# Resident Runtime Compare

- Baseline: `repeat01`
- Best: `repeat03`
- Recommendation: `best_observed:repeat03`

## Runs

| rank | label | elapsed s | read wait s | worker read s | h2d+cal s | registration s | output s |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | repeat03 | 99.8 | 3.9 | 79.5 | 17.9 | 29.8 | 5.0 |
| 2 | repeat01 | 100.0 | 4.0 | 80.0 | 18.0 | 30.0 | 5.0 |
| 3 | repeat02 | 101.2 | 4.1 | 81.0 | 18.1 | 30.3 | 5.1 |

## Comparisons

- `repeat02` / `repeat01`: elapsed ratio `1.012`, read-wait ratio `1.025`
- `repeat03` / `repeat01`: elapsed ratio `0.998`, read-wait ratio `0.975`
