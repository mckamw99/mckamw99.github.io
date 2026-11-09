# Case study B validation

Synthetic data.

| result   | check                                                                                              | detail                                                                                                     |
|:---------|:---------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------|
| PASS     | E-01: adjusted 95% CI contains the risk ratio implied by the planted hazard ratio                  | planted HR 0.7 -> expected RR 0.73; estimate 0.77 (0.64-0.94)                                              |
| PASS     | E-01: the crude estimate is further from 1 than the adjusted one (confounding by unit, as planted) | crude 0.74, adjusted 0.77                                                                                  |
| PASS     | Negative control: no effect planted on involuntary exits, and the CI includes 1                    | 0.79 (0.40-2.13)                                                                                           |
| PASS     | Sensitivity analyses all point the same way                                                        | {'landmark day 45': 0.8, 'excluding rehires': 0.77, 'RNs only': 0.62, 'any exit (voluntary or not)': 0.77} |
| PASS     | Permutation test agrees with the chi-square p-value (both < 0.05)                                  | permutation p = 0.0044, chi-square p = 0.0032                                                              |
| PASS     | E-02: landmark estimate points the planted direction                                               | planted HR 0.65; estimate 0.28 (0.06-1.39), not significant                                                |
| PASS     | E-04: early attenders reach proficiency faster, as planted                                         | medians 159.0 vs 180.0; planted means 140 vs 170 (x1.2 on specialty units)                                 |
