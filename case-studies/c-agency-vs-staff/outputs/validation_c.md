# Case study C validation

Synthetic data.

| result   | check                                                                                  | detail                                       |
|:---------|:---------------------------------------------------------------------------------------|:---------------------------------------------|
| PASS     | Simulation matches the hand calculation (no exits, full use)                           | simulation 37,879 vs hand 37,903             |
| PASS     | 2024 loaded staff rate within 0.5% of BLS ECEC total compensation ($79.53/hour worked) | model 79.7                                   |
| PASS     | Positions modeled never cover more than the agency hours bought                        | 41 positions on 13 units                     |
| PASS     | Recommendations stable under a different random seed (at least 90% identical)          | 95% identical; changed: ['U002#3', 'U004#1'] |
| PASS     | Calculator (JavaScript) matches the Python model within 10%                            | calculator 13,979 vs Python 13,322           |
