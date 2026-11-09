# Case study D validation

Synthetic data.

| result   | check                                                                  | detail                                                                                                                          |
|:---------|:-----------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------|
| PASS     | Every mismatch has a tested explanation                                | 7 mismatched facility-months                                                                                                    |
| PASS     | Mismatched months are exactly the planted ones (PI-01..03)             | ['2024-08', '2025-03', '2025-10']                                                                                               |
| PASS     | PI-02 diagnosed as a double load at Community North                    |                                                                                                                                 |
| PASS     | PI-03 diagnosed as agency accounts at Flagship Hospital                |                                                                                                                                 |
| PASS     | PI-01 diagnosed as stale data, 4 days                                  | 5 facilities differed; answer key lists 6 rows (one facility had no activity in the stale window, so its numbers didn't change) |
| PASS     | Access review finds the planted issues AX-01..03 and nothing else      | 4 findings                                                                                                                      |
| PASS     | Mockup numbers equal case study A's governed results (M1, M2, overdue) | mockup 67.3% / 81.6% / 3376.0; A 67.3% / 81.6% / 3376                                                                           |
