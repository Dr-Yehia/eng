# FDOT Multi-Case Validation v1 — Summary

Tests whether the **same parser + abnormal-pricing-risk methodology** is stable across multiple FDOT lettings.
Wording throughout: **abnormal pricing risk / pricing deviation / commercial review** — NOT fraud.

## Cases
- Required (must pass ≥3): T5850, T6603, T1900
- Specialized (attempted): T4711, E7Q32, E7U28

## Extraction reliability
- Cases extracted successfully: **4/6** | parser success rate **67%**.
- For every successfully-extracted case, all bidder grand totals reconstructed from line items match the official PDF totals exactly.

## Per-case results (extracted)
| case_id | project_type | bidders | items | winning_total_bid | exposure | crit | high | possible_unbalanced |
|---|---|---|---|---|---|---|---|---|
| T5850 | highway milling & resurfacing | 7 | 135 | 7139022.43 | 7.3% | 36 | 23 | 0 |
| T6603 | highway resurfacing | 4 | 104 | 6947336.62 | 8.8% | 27 | 19 | 1 |
| T1900 | traffic signals & roadway | 4 | 99 | 4662926.98 | 5.9% | 15 | 10 | 0 |
| E7Q32 | small bridge repair | 2 | 22 | 1728143.0 | 20.3% | 14 | 3 | 3 |

## Methodology (constant across cases)
- Primary benchmark = **non-winner bidder median** (competitive, same project/date).
- ML DDC benchmark = **supporting only** (strong≥0.85; FDOT-vs-Eurasian mismatch → near-zero strong matches; never drives flags).
- FDOT historical 6m/12m: not a joinable bulk table in the provided "2025 BID DATA PROGRAM.xlsx" (it is a per-item interactive calculator) → reserved.
- Lump-sum items separated from unit-rate items; multi-case columns on every row.

## Acceptance
- ≥3 required cases pass extraction AND risk: **YES** (3/3).
- Combined item-level + dashboard-ready + Excel report created: YES.

## Limitations
- Risk = pricing DEVIATION vs benchmarks, not proof of irregularity.
- Still a small set of cases from one DOT; broader generalization needs more lettings and DOTs.
- ML benchmark is structurally low-coverage for highway pay items; bidder-market benchmark carries the analysis.
