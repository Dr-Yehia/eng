# -*- coding: utf-8 -*-
"""Dynamic time escalation — the SAME weighted multi-index log-differential method
validated in outputs_dynamic_escalation_v1, over the FROZEN BLS snapshot (reproducible).
No forecasting: targets beyond the snapshot are clamped to the latest month, with a warning."""
import numpy as np
import pandas as pd
from . import assets

FAMILIES = ["labor", "material", "equipment", "energy", "general"]
DEFAULT_W = {"labor": 0.25, "material": 0.30, "equipment": 0.15, "energy": 0.10, "general": 0.20}


def _family_code_map():
    idx = assets.indices()
    m = {}
    for fam, code in idx[["index_family", "index_code"]].drop_duplicates().itertuples(index=False):
        m["general" if fam == "general_construction" else fam] = code
    return m


def weights_from_composition(composition: dict = None):
    """Per-spec signal shares; falls back to documented defaults when no composition."""
    c = composition or {}
    sig = {"labor": float(c.get("labor_hours") or 0), "material": float(c.get("material_count") or 0),
           "equipment": float((c.get("machine_count") or 0)) + float((c.get("operator_count") or 0)),
           "energy": float(c.get("electricity_kwh") or 0), "general": 1.0}
    tot = sum(sig.values())
    if tot <= 1.0 + 1e-9:  # only the general baseline present -> defaults
        return dict(DEFAULT_W), "default division-mix weights (no composition provided)"
    return {k: v / tot for k, v in sig.items()}, "weights from user composition signals"


def escalate(price: float, target_date, base_month: str = "2026-03-01", composition: dict = None):
    idx = assets.indices()
    codes = _family_code_map()
    latest = idx["date"].max()
    tgt = pd.Timestamp(target_date).replace(day=1)
    warnings = []
    if tgt > latest:
        warnings.append(f"Target {tgt:%Y-%m} is beyond the frozen index snapshot ({latest:%Y-%m}); "
                        "factor uses the latest available month (no forecasting).")
        tgt = latest
    if tgt < pd.Timestamp(base_month):
        warnings.append("Target precedes the DDC base month; reverse escalation applied.")
    W, wnote = weights_from_composition(composition)
    F, lnF = {}, 0.0
    for fam in FAMILIES:
        s = idx[idx.index_code == codes[fam]].set_index("date")["index_value"]
        b, t = float(s.get(pd.Timestamp(base_month), np.nan)), float(s.get(tgt, np.nan))
        F[fam] = t / b if np.isfinite(t / b) else 1.0
        lnF += W[fam] * np.log(F[fam])
    factor = float(np.exp(lnF))
    return {"escalation_factor": factor, "escalated_price": max(price * factor, 1e-6),
            "F_by_family": F, "weights": W, "weights_note": wnote,
            "base_month": base_month, "target_month_used": f"{tgt:%Y-%m-01}",
            "index_as_of": f"{latest:%Y-%m}", "warnings": warnings}
