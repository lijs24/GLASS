# GLASS Windows Gate307 Preflight

Windows portable packages for GLASS.

- Source stamp: `aa63510`
- Package count: `4`

## Assets

| Label | Size bytes | SHA256 |
| --- | ---: | --- |
| cuda13 | 341358345 | `bc5ebaf5247f7a7a513d1ff2ba3f4445d30c373c1e5e955cbfe7f01a9f0de273` |
| cuda12 | 341223006 | `72f674ac5613d1618db5aebdbcab99711acefc887ff25b884db85c825e6ccf31` |
| cuda11 | 342200540 | `2d0a68b53ffc92dadfc48e4404a81facbcb5d49f7bad1b89b79ce9337a42f681` |
| cpu | 296231852 | `32c7743c4ec2ed73ff1dd990c120ac7d8b0234a80db8b1e446627fd82ef5991d` |

## Recommended Install Order

Try `cuda13`, then `cuda12`, then `cuda11`, then `cpu`.

## Windows Release Matrix Evidence

- Windows release matrix: `release_matrix_ready` passed `True`
- Primary package: `cuda13` packages `cuda11, cuda12, cuda13, cpu`
- Default promotion: `default_promotion_ready` passed `True`
- Default route contract: `True` checks `4` speedup `28.75107894736842`
- StackEngine default contract: ready `True` phase2-check `True` gaps `0` blockers `0`
- Rejection sample accounting: `passed` failed `0`
- Sample accounting closure: `passed` present `0` failed `0`

## Phase 2 Handoff Evidence

- Phase 2 status: `green` gate `304`
- Resident registration fast path: `present` contract `passed` mode `similarity_cuda_triangle`
- Fast path details: descriptor batch `True`, pixel refine batch `True`, warp batch `True` frames `188`, copy `default_stream_async_device_to_device`
- Pipeline DQ contract: `passed` passed `True` DQ `True`
- Pipeline pixel verification: `True` DQ pixels `True` coverage `True` rejection `True`
- Pipeline rejection sample accounting: `passed` check `True` failed `0`
- Pipeline sample accounting closure: `passed` check `True` failed `0`
- StackEngine default contract: `passed` check `True` gaps `0` blockers `0`
- StackEngine default recommendation: `stack_engine_default_ready` promotion `stack_engine_default_ready`
- Default-change decision: `default_change_ready` ready `True` recommendation `promote_default_candidate`
- Runtime repeat evidence: runs `3`, best `gate218_default_repeat02` `22.598500299995067` s, ratio `1.053510511049479`
- Phase 2 status compare: `None` baseline `None` candidate `None`
