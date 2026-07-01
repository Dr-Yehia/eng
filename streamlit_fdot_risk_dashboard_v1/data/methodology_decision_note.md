# Methodology Decision Note — Integrated Dual-Benchmark Risk (v2)

**The FDOT abnormal-pricing-risk layer is NOT driven by the ML benchmark**, because reliable ML matching
coverage for FDOT roadway pay items is approximately 0.0% (strong matches).
Instead, risk is evaluated with **two independent, high-coverage benchmarks**:

1. **Contractor market** — the non-winner bidder median (internal, competitive, same project & date).
2. **FDOT historical 2024 statewide weighted average** — external, official, prior to the 2025 lettings (look-ahead-safe). Window: Contract Type: ('CC')    Statewide.

ML DDC is retained **only as supporting evidence** where a strong item match exists.

## Coverage
- Market: 100% · Historical: **97%** · ML strong: 0.0%.

## Agreement between the two benchmarks
- Exact-flag agreement **34%**, elevated-binary **Cohen κ=0.36**, weighted κ=0.29, deviation **Spearman=0.56**.
- **Confirmed-by-both (high-confidence risk): 105** · Historical-only: 87 · Market-only: 30.

## Thresholds (data-driven, not only fixed rules)
Classification uses fixed % **and** robust z-score **and** per-benchmark P75/P90/P95 of |deviation|.
Market P95=138% · Historical P95=275%.

## Framing (honest, strengthened)
> The ML model is the engine for the **general DDC unit-price benchmark, time escalation and regional calibration**.
> The **bid-tab abnormal-pricing-risk layer** is driven by **two independent real benchmarks (competitive market + official FDOT historical)** whose agreement defines confidence; ML is a supporting signal only.
> This is a stronger and more defensible contribution than claiming ML detects abnormal pricing on highway items.

Wording is *abnormal pricing risk / commercial review* — never *fraud*.
