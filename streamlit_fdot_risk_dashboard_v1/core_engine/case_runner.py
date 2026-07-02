# -*- coding: utf-8 -*-
"""Run a FULL case (ready or uploaded) through the validated dual-benchmark risk logic, item by item.
No new equations: bidder-market (non-winner median) + FDOT historical 2024 + statistical thresholds,
identical to integrated_risk_v2. Streamlit only calls run_case() / validate_bidtab()."""
import numpy as np
import pandas as pd
from . import assets
from .matching_engine import norm_item_id
from .risk_engine import _flag_stat, _flag_fixed, ORDER

ELEV = {"High", "Critical"}
TEMPLATE_COLS = ["line_no", "item_id", "description", "section_name", "unit", "quantity", "is_lump_sum"]


def bidder_price_cols(df):
    return [c for c in df.columns if str(c).lower().startswith("bidder") and "price" in str(c).lower()]


def validate_bidtab(df: pd.DataFrame) -> dict:
    """Validation BEFORE risk (per spec). Returns {ok, errors[], warnings[], n_items, n_bidders}."""
    errors, warnings = [], []
    miss = [c for c in ["description", "unit", "quantity"] if c not in df.columns]
    if miss:
        errors.append(f"Missing required columns: {miss}")
    bcols = bidder_price_cols(df)
    has_actual = "actual_unit_price" in df.columns
    if not bcols and not has_actual:
        errors.append("Provide either bidder price columns (bidder1_unit_price, …) OR an actual_unit_price column.")
    if "quantity" in df.columns and (pd.to_numeric(df["quantity"], errors="coerce") <= 0).any():
        warnings.append("Some quantities are ≤ 0 (lump-sum items are allowed to be 1).")
    if len(df) == 0:
        errors.append("No item rows found.")
    if len(df) > 2000:
        warnings.append("More than 2000 rows — only the first 2000 will be processed.")
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "n_items": int(len(df)), "n_bidders": len(bcols), "mode": "bid_tab" if bcols else "single_price"}


def _stats(series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    med = float(s.median()); mad = float((s - med).abs().median())
    ab = s.abs()
    return {"p75": float(ab.quantile(.75)) if len(ab) else np.inf,
            "p90": float(ab.quantile(.90)) if len(ab) else np.inf,
            "p95": float(ab.quantile(.95)) if len(ab) else np.inf, "median": med, "mad": mad}


def run_case(df: pd.DataFrame, winner_col: str = None, winning_total: float = None):
    """Item-by-item dual-benchmark risk. df has the template cols + bidder price cols OR actual_unit_price.
    Returns (result_df, summary_dict)."""
    df = df.head(2000).copy().reset_index(drop=True)
    for c in TEMPLATE_COLS:
        if c not in df: df[c] = np.nan
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0.0)
    df["is_lump_sum"] = df["is_lump_sum"].fillna(False).astype(bool) if "is_lump_sum" in df else (df["unit"].astype(str).str.upper() == "LS")
    bcols = bidder_price_cols(df)
    for c in bcols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # winner (actual) price
    if bcols:
        wc = winner_col if (winner_col in bcols) else bcols[0]
        df["actual_unit_price"] = df[wc]
        M = df[bcols].values.astype(float)
        nwc = [c for c in bcols if c != wc]
        df["bidder_market_median"] = np.nanmedian(M, axis=1)
        df["non_winner_median"] = np.nanmedian(df[nwc].values.astype(float), axis=1) if nwc else df["bidder_market_median"]
        df["bidder_low"] = np.nanmin(M, axis=1); df["bidder_high"] = np.nanmax(M, axis=1)
    else:
        df["actual_unit_price"] = pd.to_numeric(df["actual_unit_price"], errors="coerce")
        df["non_winner_median"] = np.nan; df["bidder_market_median"] = np.nan
        df["bidder_low"] = np.nan; df["bidder_high"] = np.nan
    wtotal = float(winning_total) if winning_total else float(np.nansum(df["actual_unit_price"] * np.where(df["is_lump_sum"], 1.0, df["quantity"])))

    # FDOT historical benchmark
    H = assets.fdot_historical()
    def hist(row):
        iid = str(row.get("item_id", "") or "")
        if not iid.strip(): return (np.nan, "no_item_id")
        k = norm_item_id(iid)
        if k not in H.index: return (np.nan, "no_match")
        r = H.loc[k]
        return (float(r["wavg"]), "matched") if str(row["unit"]).strip().upper() == str(r["hunit"]).strip().upper() else (np.nan, "unit_mismatch")
    hv = df.apply(hist, axis=1, result_type="expand")
    df["historical_benchmark"] = hv[0]; df["historical_match_status"] = hv[1]

    # deviations
    df["deviation_vs_market"] = (df["actual_unit_price"] - df["non_winner_median"]) / df["non_winner_median"].replace(0, np.nan) * 100
    df["deviation_vs_historical"] = (df["actual_unit_price"] - df["historical_benchmark"]) / df["historical_benchmark"].replace(0, np.nan) * 100

    # thresholds from THIS case's unit-rate items (data-driven, same rule set as validated)
    ur = df[~df["is_lump_sum"]]
    thm = _stats(ur["deviation_vs_market"]); thh = _stats(ur["deviation_vs_historical"])
    df["market_risk_flag"] = df["deviation_vs_market"].map(lambda d: _flag_stat(d, thm))
    df["historical_risk_flag"] = df["deviation_vs_historical"].map(lambda d: _flag_stat(d, thh))

    def combine(r):
        m, h = r["market_risk_flag"], r["historical_risk_flag"]
        m_av, h_av = m in ORDER, h in ORDER
        m_e, h_e = m in ELEV, h in ELEV
        if not m_av and not h_av: ev = "no_benchmark"
        elif m_e and h_e: ev = "confirmed_by_both"
        elif h_e and not m_e: ev = "historical_only"
        elif m_e and not h_e: ev = "market_only"
        else: ev = "low_evidence"
        ranks = [ORDER.index(x) for x in (m, h) if x in ORDER]
        cflag = ORDER[max(ranks)] if ranks else "Not available"
        conf = ("High" if ev == "confirmed_by_both" else "Medium" if ev in ("historical_only", "market_only") else "Low")
        if r["is_lump_sum"] or (m_av ^ h_av): conf = "Low"
        return ev, cflag, conf
    cc = df.apply(combine, axis=1, result_type="expand")
    df["evidence_class"], df["combined_risk_flag"], df["risk_confidence"] = cc[0], cc[1], cc[2]

    ref = df["non_winner_median"].fillna(df["historical_benchmark"]).fillna(df["actual_unit_price"])
    qeff = np.where(df["is_lump_sum"], 1.0, df["quantity"])
    df["overpricing_exposure"] = np.maximum(df["actual_unit_price"] - ref, 0) * qeff
    prim = df["deviation_vs_market"].fillna(df["deviation_vs_historical"])
    df["risk_direction"] = np.where(df["combined_risk_flag"].isin(ELEV),
                                    np.where(prim > 0, "overpricing", np.where(prim < 0, "underpricing", "mixed")), "n/a")
    df["data_quality_flag"] = np.where(df["is_lump_sum"], "lump_sum",
                                np.where(df["historical_match_status"] == "matched", "ok", "no_historical_match"))
    def action(r):
        if r["is_lump_sum"]: return "Review lump-sum pricing separately"
        if r["risk_confidence"] == "Low": return "Manual review required"
        if r["combined_risk_flag"] in ELEV:
            return ("Request rate breakdown / commercial review (overpricing)" if r["risk_direction"] == "overpricing"
                    else "Review potential unbalanced underpricing" if r["risk_direction"] == "underpricing"
                    else "Commercial review (mixed signal)")
        return {"Normal": "Accept", "Watch": "Monitor item", "Moderate": "Review unit rate basis"}.get(r["combined_risk_flag"], "Review")
    df["recommended_action"] = df.apply(action, axis=1)

    summary = {
        "n_items": int(len(df)), "n_bidders": len(bcols), "winning_total_bid": wtotal,
        "mode": "bid_tab" if bcols else "single_price",
        "overpricing_exposure": float(df["overpricing_exposure"].sum()),
        "exposure_pct_of_bid": float(df["overpricing_exposure"].sum() / wtotal * 100) if wtotal else np.nan,
        "risk_distribution": {k: int((df["combined_risk_flag"] == k).sum()) for k in ORDER},
        "confirmed_by_both": int((df["evidence_class"] == "confirmed_by_both").sum()),
        "historical_only": int((df["evidence_class"] == "historical_only").sum()),
        "market_only": int((df["evidence_class"] == "market_only").sum()),
        "historical_coverage_pct": float((df["historical_match_status"] == "matched").mean() * 100),
        "thresholds": {"market": thm, "historical": thh},
    }
    return df, summary
