# Paper-result reproduction audit

This table compares printed values with the outputs generated or archived in this package.

| Section | Metric | Paper | Reproduced | Status | Note |
|---|---|---:|---:|---|---|
| Corpus audit | A2 tokens | 297 | 297 | exact |  |
| Corpus audit | A2 types | 195 | 195 | exact |  |
| Corpus audit | Herbal_A tokens | 7694 | 7694 | exact |  |
| Corpus audit | Herbal_A types | 2270 | 2270 | exact |  |
| Corpus audit | full_VM_ngram tokens | 37608 | 37608 | exact |  |
| Corpus audit | full_VM_ngram types | 7457 | 7457 | exact |  |
| Corpus audit | strict_VM_attestation tokens | 37597 | 37597 | exact |  |
| Corpus audit | strict_VM_attestation types | 7455 | 7455 | exact |  |
| Table 1 | Analyzed tokens | 6765 | 6765 | exact_to_printed_precision |  |
| Table 1 | Covered tokens | 6747 | 6747 | exact_to_printed_precision |  |
| Table 1 | Observed types | 2012 | 2012 | exact_to_printed_precision |  |
| Table 1 | Covered types | 1994 | 1994 | exact_to_printed_precision |  |
| Table 1 | Transitions | 20207 | 20207 | exact_to_printed_precision |  |
| Table 1 | Forward rate | 0.6164 | 0.6163705646558123 | exact_to_printed_precision |  |
| Table 1 | Same-layer rate | 0.2323 | 0.23234522690156875 | exact_to_printed_precision |  |
| Table 1 | Backward rate | 0.1513 | 0.1512842084426189 | exact_to_printed_precision |  |
| Table 1 | Randomized backward mean | 0.3965 | 0.3964944365813826 | exact_to_printed_precision |  |
| Table 1 | Zero-back words | 0.6172 | 0.617163183637172 | exact_to_printed_precision |  |
| Table 1 | Zero/one-back words | 0.9342 | 0.9341929746554024 | exact_to_printed_precision |  |
| Table 1 | Minimum bifolium back rate | 0.1039 | 0.1039426523297491 | exact_to_printed_precision |  |
| Table 1 | Maximum bifolium back rate | 0.1919 | 0.19190283400809716 | exact_to_printed_precision |  |
| Table 1 | Randomization plus-one tail | 4e-05 | 3.999920001599968e-05 | exact_to_printed_precision |  |
| Table 2 | Layer only top1 | 0.2738 | 0.27380952380952384 | exact_to_printed_precision |  |
| Table 2 | Layer only top3 | 0.5714 | 0.5714285714285714 | exact_to_printed_precision |  |
| Table 2 | Layer only one_to_one | 0.2262 | 0.22619047619047616 | exact_to_printed_precision |  |
| Table 2 | Full top1 | 0.381 | 0.38095238095238093 | exact_to_printed_precision |  |
| Table 2 | Full top3 | 0.7619 | 0.7619047619047619 | exact_to_printed_precision |  |
| Table 2 | Full one_to_one | 0.4286 | 0.4285714285714286 | exact_to_printed_precision |  |
| N-gram bifolium classification | 2-gram top1 | 0.3127 | 0.31397619047619335 | monte_carlo_near_match | The original 2,000 holdout configurations and seed were not preserved; a new fixed seed is archived. |
| N-gram bifolium classification | 2-gram one_to_one | 0.2911 | 0.29069047619047833 | monte_carlo_near_match | The original 2,000 holdout configurations and seed were not preserved; a new fixed seed is archived. |
| N-gram bifolium classification | 2-gram top3 | 0.6177 | 0.6153571428571454 | monte_carlo_near_match | The original 2,000 holdout configurations and seed were not preserved; a new fixed seed is archived. |
| N-gram bifolium classification | 3-gram top1 | 0.2559 | 0.25530952380952515 | monte_carlo_near_match | The original 2,000 holdout configurations and seed were not preserved; a new fixed seed is archived. |
| Next-state prediction | Bigram bits/state | 2.2931 | 2.293238393944109 | reconstructed_near_match | Additive smoothing alpha=0.1 and page-fold seed 123 are now explicit; the original choices were not archived. |
| Next-state prediction | Trigram bits/state | 2.1691 | 2.169472300692944 | reconstructed_near_match | Additive smoothing alpha=0.1 and page-fold seed 123 are now explicit; the original choices were not archived. |
| Table 3 | bigram_jsd | 0.03892 | 0.03898054599993121 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | eight_plus_rate | 0.0117 | 0.011693602693602693 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | hapax_legomena | 136.17 | 136.028 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | mean_word_length | 4.0186 | 4.01826936026936 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | neutral_restart_gallows | 0.0277 | 0.02878125 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | one_character_rate | 0.0446 | 0.04452525252525252 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | paragraph_start_gallows | 1.0 | 1.0 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | trigram_jsd | 0.10608 | 0.10608769254975516 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | word_boundary_jsd | 0.11462 | 0.11375889901035047 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | word_length_sd | 1.6186 | 1.6193038616614208 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Table 3 | word_types | 188.54 | 188.411 | stochastic_near_match | The original simulation seed was not preserved; the package archives seed 20260817. |
| Shelf attestation | A2 | 0.55 | 0.5503501683501684 | stochastic_near_match | The original simulation seed was not preserved; the package archives a separate deterministic stream. |
| Shelf attestation | HerbalA_outside_A2 | 0.1752 | 0.17465252525252525 | stochastic_near_match | The original simulation seed was not preserved; the package archives a separate deterministic stream. |
| Shelf attestation | Outside_A2_total | 0.2205 | 0.22015420875420877 | stochastic_near_match | The original simulation seed was not preserved; the package archives a separate deterministic stream. |
| Shelf attestation | Unattested | 0.2295 | 0.22949562289562292 | stochastic_near_match | The original simulation seed was not preserved; the package archives a separate deterministic stream. |
| Shelf attestation | VM_outside_HerbalA | 0.0453 | 0.0455016835016835 | stochastic_near_match | The original simulation seed was not preserved; the package archives a separate deterministic stream. |
| Shelf attestation | VM_total | 0.7705 | 0.7705043771043771 | stochastic_near_match | The original simulation seed was not preserved; the package archives a separate deterministic stream. |
| Table 4 nulls | uni VM_total | 0.1237 | 0.1236983164983165 | exact_archived_output |  |
| Table 4 nulls | uni Outside_A2_total | 0.0897 | 0.0896861952861952 | exact_archived_output |  |
| Table 4 nulls | bi VM_total | 0.7726 | 0.7725838383838384 | exact_archived_output |  |
| Table 4 nulls | bi Outside_A2_total | 0.286 | 0.2860309764309764 | exact_archived_output |  |
| Table 4 nulls | tri VM_total | 0.8762 | 0.8762175084175083 | exact_archived_output |  |
| Table 4 nulls | tri Outside_A2_total | 0.228 | 0.2280026936026935 | exact_archived_output |  |
| D-G reassignment | Observed new active compartments | 99 | 99 | exact |  |
| D-G reassignment | Reassignment mean | 108.17 | 108.16666666666667 | exact_to_printed_precision | The paper result uses the stored stable-22 state definition (VM23 excluding rare g). |
| D-G reassignment | One-sided exact p | 0.0056 | 0.005555555555555556 | exact_to_printed_precision |  |
| D-G sensitivity | VM23 reassignment mean |  | 109.16666666666667 | new_sensitivity | Including g changes the mean to 109.17 while leaving observed=99 and p=1/180. |
| Inventory | Main tablets | 600 | 600 | exact |  |
| Inventory | Safety tablets | 14 | 14 | exact |  |
| Inventory audit | Reachable tablets under published rules |  | 584 | new_audit | Sixteen physical tablets are unreachable under the printed state-update and stopping rules. |
| Inventory audit | Reachable empty states |  | 0 | new_audit |  |
| A-2 fitting inputs | BOUNDARY empirical events | 257 | 257 | exact |  |
| A-2 fitting inputs | INTERNAL empirical events | 604 | 604 | exact |  |
| A-2 fitting inputs | RESTART empirical events | 32 | 32 | exact |  |
| A-2 fitting inputs | SECOND empirical events | 283 | 283 | exact |  |
| A-2 fitting inputs | START empirical events | 8 | 8 | exact |  |
