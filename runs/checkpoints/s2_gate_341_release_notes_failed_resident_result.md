# GLASS S2 Gate 341 Failed Fixture

Windows portable packages for GLASS.

- Source stamp: `s2-gate-341`
- Package count: `4`

## Assets

| Label | Size bytes | SHA256 |
| --- | ---: | --- |
| cuda13 | 20 | `81ef7633b1c7d700aff468c131055ee625b5f2efcc31b67ebaa1a1b35efb3d98` |
| cuda12 | 20 | `a661671be01d3028d5580c506adf858600c1252c621cdc8d6dfc4a462e3b7fd6` |
| cuda11 | 20 | `ca9d8a29bf75e27ef6e0d7eab2d6ee23496e78314be793293f219f2aa9918256` |
| cpu | 17 | `843662196aad1d87a22bfff89308b04f5b579a43a9c945d823ae7a91a634a48e` |

## Recommended Install Order

Try `cuda13`, then `cuda12`, then `cuda11`, then `cpu`.

## Windows Release Matrix Evidence

- Windows release matrix: `blocked` passed `False`
- Primary package: `cuda13` packages `cuda11, cuda12, cuda13, cpu`
- Default promotion: `blocked` passed `False`
- Default route contract: `True` checks `4` speedup `28.75`
- Release direct publication guard: ready `True` check `True` source `explicit_resident_artifacts_json`/`resident_artifacts_json_fallback` lights `200`
- Default-promotion release direct guard: ready `True` check `True` lights `200`
- StackEngine default contract: ready `True` phase2-check `True` gaps `0` blockers `0`
- Resident fastpath release handoff: ready `True` raw `passed` phase2 `passed` agreement `True` checks `23`
- Resident result contract: ready `False` status `failed` phase2 `False` required `1` failed `1`
- Rejection sample accounting: `passed` failed `0`
- Sample accounting closure: `passed` present `1` failed `0`
