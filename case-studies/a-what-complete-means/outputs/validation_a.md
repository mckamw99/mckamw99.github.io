# Case study A validation

Synthetic data.

| result   | check                                                         | detail                                                                      |
|:---------|:--------------------------------------------------------------|:----------------------------------------------------------------------------|
| PASS     | Step 0 equals the published April 2025 scorecard              | bridge 16106/20780 vs published 16106/20780                                 |
| PASS     | SQL recompute matches pandas by facility (2025)               | SQL 2469/3666 vs pandas 2469/3666                                           |
| PASS     | Every linked manual account went to the right person          | 66 of 66 correct; 33 of 99 left unresolved                                  |
| INFO     | Identity matches by rule                                      | {'name_and_complementary_records': '27/27', 'name_and_employment': '39/39'} |
| PASS     | C13 finds exactly the planted DQ-01 rows                      | 69 vs 69                                                                    |
| PASS     | C12 finds exactly the planted DQ-02 rows                      | 328 vs 328                                                                  |
| PASS     | C07 finds exactly the planted DQ-03 rows                      | 164 vs 164                                                                  |
| PASS     | C08 finds exactly the planted DQ-04 rows                      | 281 vs 281                                                                  |
| PASS     | C10 finds exactly the planted DQ-06 rows                      | 740 vs 740                                                                  |
| PASS     | C01 finds exactly the planted DQ-08 rows                      | 6 vs 6                                                                      |
| PASS     | C14 finds exactly the planted DQ-09 rows                      | 2 vs 2                                                                      |
| PASS     | C04 finds exactly the planted DQ-10 rows                      | 126 vs 126                                                                  |
| PASS     | C02 + C03 account for every planted duplicate account (DQ-07) | 66 + 33 vs 99                                                               |
| PASS     | C06 catches the planted 2024 reload (DQ-05)                   | 436 people with a repeated AC-04-2024 campaign row vs 436 planted           |
| INFO     | Trace written for human review                                | outputs/trace_sample.md                                                     |
