# Reproduced quantitative results

## Corpus audit

| Corpus | Tokens | Types |
|---|---:|---:|
| A2 | 297 | 195 |
| Herbal_A | 7694 | 2270 |
| full_VM_ngram | 37608 | 7457 |
| strict_VM_attestation | 37597 | 7455 |

## Seven-layer directionality (Table 1)

- analyzed/covered tokens: 6765 / 6747
- transitions: 20207
- forward / within / backward: 61.637056% / 23.234523% / 15.128421%
- randomized backward mean: 39.649444%
- count <= observed: 1 / 50000; plus-one tail 3.99992e-05

## Seven-layer bifolium classification (Table 2)

| Model | Top 1 | Top 3 | One-to-one |
|---|---:|---:|---:|
| Layer only | 27.38% | 57.14% | 22.62% |
| Full | 38.10% | 76.19% | 42.86% |

## N-gram bifolium classification

| n | Top 1 | Top 3 | One-to-one | Mean rank |
|---:|---:|---:|---:|---:|
| 2 | 31.3976% | 61.5357% | 29.0690% | 3.8970 |
| 3 | 25.5310% | 57.4500% | 26.3810% | 4.4011 |
| 4 | 22.6214% | 48.2024% | 21.5905% | 5.2624 |
| 5 | 20.4071% | 38.9167% | 19.1024% | 6.5031 |

## Next-state prediction

- bigram: 2.293238 bits/state
- trigram: 2.169472 bits/state
- improvement: 0.123766 bits/state

## Exact inventory and reachability

- main shelf / START: 600 / 8
- reachable / unreachable physical main-shelf tablets: 584 / 16
- reachable empty states: 0

## A-2 shelf fit (1,000 runs)

| Metric | Mean | Paper target |
|---|---:|---:|
| bigram_jsd | 0.038980546 | 0.03892 |
| eight_plus_rate | 0.011693603 | 0.0117 |
| hapax_legomena | 136.028 | 136.17 |
| mean_word_length | 4.0182694 | 4.0186 |
| neutral_restart_gallows | 0.02878125 | 0.0277 |
| one_character_rate | 0.044525253 | 0.0446 |
| paragraph_start_gallows | 1 | 1.0 |
| trigram_jsd | 0.10608769 | 0.10608 |
| word_boundary_jsd | 0.1137589 | 0.11462 |
| word_length_sd | 1.6193039 | 1.6186 |
| word_types | 188.411 | 188.54 |

## A-2 shelf attestation (5,000 runs)

| Metric | Mean | Paper target |
|---|---:|---:|
| A2 | 0.55035017 | 0.55 |
| HerbalA_outside_A2 | 0.17465253 | 0.1752 |
| Outside_A2_total | 0.22015421 | 0.2205 |
| Unattested | 0.22949562 | 0.2295 |
| VM_outside_HerbalA | 0.045501684 | 0.0453 |
| VM_total | 0.77050438 | 0.7705 |

## D–G exact reassignment

- stored stable-22 definition: observed 99, mean 108.166667, p=0.00555556
- VM23 sensitivity: observed 99, mean 109.166667, p=0.00555556

See `outputs/audits/paper_results_comparison.md` and `LIMITATIONS.md` for exact target comparisons and caveats.
