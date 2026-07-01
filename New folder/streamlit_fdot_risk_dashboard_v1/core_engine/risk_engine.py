# -*- coding: utf-8 -*-
"""Abnormal-pricing-risk assessment for a manually entered item — the SAME classification
logic and statistical thresholds validated in integrated_risk_v2 (fixed% + robust-z + P75/90/95).
For single-item entry there is NO bidder market; benchmarks are FDOT-historical (primary when
matched) and the model benchmark (supporting). Wording: abnormal pricing risk — never fraud."""
import numpy as np
import pandas as pd
from . import assets

ORDER = ["Normal", "Watch", "Moderate", "High", "Critical"]


def _flag_stat(dev, th):
    """Identical rule set to integrated_risk_v2 (validated)."""
    if dev is None or (isinstance(dev, float) and not np.isfinite(dev)):
        return "Not available"
    ad = abs(dev)
    z = (dev - th["median"]) / (1.4826 * th["mad"]) if th["mad"] > 0 else np.nan
    az = abs(z) if np.isfinite(z) else 0
    if ad > 60 or az >= 3 or ad >= th["p95"]: return "Critical"
    if ad > 35 or az >= 2 or ad >= th["p90"]: return "High"
    if ad > 20 or az >= 1.5 or ad >= th["p75"]: return "Moderate"
    if ad > 10 or az >= 1: return "Watch"
    return "Normal"


def _flag_fixed(dev):
    """Fixed-% only (used for the model-benchmark deviation — no validated percentile set for it)."""
    if dev is None or not np.isfinite(dev): return "Not available"
    ad = abs(dev)
    return ("Critical" if ad > 60 else "High" if ad > 35 else
            "Moderate" if ad > 20 else "Watch" if ad > 10 else "Normal")


def assess(actual_unit_price: float, quantity: float, benchmark_price: float,
           historical: dict = None, is_lump_sum: bool = False, benchmark_confidence: str = "Medium"):
    """historical = output of matching_engine.match_fdot_historical (or None).
    benchmark_confidence: prediction-engine tier; if 'Low', the model benchmark is shown
    but NEVER counted as confirming evidence (honesty guard)."""
    th = assets.risk_thresholds()
    qty = 1.0 if is_lump_sum else float(quantity or 1.0)
    out = {"benchmarks": {}, "wording": "abnormal pricing risk — commercial review (not fraud)"}

    dev_h, flag_h = None, "Not available"
    if historical and historical.get("status") == "matched" and historical.get("wavg"):
        dev_h = (actual_unit_price - historical["wavg"]) / historical["wavg"] * 100
        flag_h = _flag_stat(dev_h, th["historical"])
        out["benchmarks"]["fdot_historical_2024"] = {
            "price": historical["wavg"], "deviation_pct": dev_h, "flag": flag_h,
            "note": "official statewide 2024 weighted average (not time-adjusted)"}

    dev_b = (actual_unit_price - benchmark_price) / benchmark_price * 100 if benchmark_price else None
    flag_b = _flag_fixed(dev_b)
    out["benchmarks"]["model_benchmark_escalated"] = {
        "price": benchmark_price, "deviation_pct": dev_b, "flag": flag_b,
        "note": "expected benchmark unit price (validated engines) — supporting when historical is matched"}

    # combined: historical primary when matched; model benchmark can confirm ONLY if its own confidence isn't Low
    b_usable = flag_b in ORDER and benchmark_confidence != "Low"
    if flag_h in ORDER:
        agree = b_usable and (flag_b in {"High", "Critical"}) == (flag_h in {"High", "Critical"})
        primary, primary_dev, evid = flag_h, dev_h, ("confirmed_by_both" if agree else "historical_primary")
        conf = "High" if agree else "Medium"
    elif b_usable:
        primary, primary_dev, evid, conf = flag_b, dev_b, "model_benchmark_only", "Medium-Low"
    else:
        primary, primary_dev, evid, conf = "Not available", None, "no_benchmark", "Low"
    if not b_usable and flag_b in ORDER:
        out["benchmarks"]["model_benchmark_escalated"]["note"] += " — LOW prediction confidence: shown for reference only, not used as evidence"
    if is_lump_sum:
        conf = "Low"

    ref = (historical or {}).get("wavg") or benchmark_price or actual_unit_price
    exposure = max(actual_unit_price - ref, 0) * qty
    under = min(actual_unit_price - ref, 0) * qty
    direction = ("overpricing" if (primary_dev or 0) > 0 else
                 "underpricing" if (primary_dev or 0) < 0 else "n/a") if primary in ORDER else "n/a"
    action = ("Review lump-sum pricing separately" if is_lump_sum else
              "Manual review required" if conf == "Low" else
              "Request rate breakdown / commercial review (overpricing)" if primary in {"High", "Critical"} and direction == "overpricing" else
              "Review potential unbalanced underpricing" if primary in {"High", "Critical"} and direction == "underpricing" else
              {"Normal": "Accept", "Watch": "Monitor item", "Moderate": "Review unit rate basis"}.get(primary, "Review"))
    out.update({"combined_risk_flag": primary, "primary_deviation_pct": primary_dev,
                "evidence_class": evid, "risk_confidence": conf, "risk_direction": direction,
                "overpricing_exposure": exposure, "underpricing_amount": under,
                "recommended_action": action})
    return out
