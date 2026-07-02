# -*- coding: utf-8 -*-
"""Live benchmark prediction using the SAME saved XGBoost model + preprocessing pipeline
that was validated in modeling_v1_1 (GroupKFold, no leakage). No new equations here:
missing numeric features are imputed with documented division medians and the run is
flagged with an input-completeness confidence tier (never silently confident)."""
import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from . import assets
from .matching_engine import match_ddc

UNIT_DIM = {"CY": "volume", "M3": "volume", "GAL": "volume",
            "SF": "area", "SY": "area", "M2": "area", "AC": "area",
            "LF": "length", "M": "length", "MI": "length", "MILE": "length",
            "TN": "weight", "TON": "weight", "LB": "weight", "KG": "weight",
            "EA": "count", "AS": "count", "PI": "count", "LO": "count",
            "LS": "lumpsum", "DA": "time", "ED": "time", "HR": "time", "MO": "time"}


def _dimension(unit: str) -> str:
    return UNIT_DIM.get(str(unit).strip().upper(), "unknown")


def _confidence(has_item_id_match: bool, has_composition: bool, ddc_score: float) -> tuple:
    """Input-completeness confidence tier (per reviewer's table)."""
    if has_item_id_match:
        return "High", "FDOT item_id matched to the official 2024 historical benchmark."
    if has_composition and ddc_score >= 0.50:
        return "Medium-High", "Description + resource composition provided; ML uses its validated composition features."
    if ddc_score >= 0.50:
        return "Medium-Low", ("Preliminary estimate — resource composition is missing; numeric features were "
                              "imputed with division medians. The validated model draws most of its accuracy "
                              "from composition, so treat this as indicative only.")
    return "Low", "No reliable benchmark — weak catalog match and no composition. Manual review required."


def predict_benchmark(description: str, unit: str, division: str = None, composition: dict = None):
    """Returns the expected benchmark unit price at the DDC base date (2026-03) + interval + provenance.
    composition (all optional): material_count, machine_count, operator_count, labor_hours, electricity_kwh,
                                resource_names (text)."""
    composition = composition or {}
    schema = assets.feature_schema()
    NUM, BOOL, CATF = schema["numeric_features"], schema["boolean_features"], schema["categorical_features"]
    pre = assets.pipeline()
    ddc = match_ddc(description, top_k=3)
    best = ddc[0]
    div = division or (best["masterformat_division"] if best["score"] >= 0.50 else "GLOBAL")

    # --- numeric features: division medians (documented imputation), overridden by user composition ---
    dd = assets.division_defaults()
    base = (dd.loc[div] if div in dd.index else dd.loc["GLOBAL"]).copy()
    imputed = [c for c in NUM]
    ov = {"material_count": "material_count", "machine_count": "machine_count",
          "operator_count": "operator_count", "labor_hours": "total_labor_hours_all_personnel",
          "electricity_kwh": "electricity_kwh"}
    for k, col in ov.items():
        if composition.get(k) is not None and col in base.index:
            base[col] = float(composition[k]); imputed.remove(col) if col in imputed else None
    has_comp = any(composition.get(k) is not None for k in ov)

    row = {c: float(base.get(c, 0.0)) for c in NUM}
    row.update({
        "has_material": bool(composition.get("material_count", 0) or 0) or bool(base.get("material_count", 0) > 0),
        "has_machine": bool(composition.get("machine_count", 0) or 0) or bool(base.get("machine_count", 0) > 0),
        "has_labor": True, "missing_operator_info": composition.get("operator_count") is None,
        "missing_mass_info": True, "missing_electricity_info": composition.get("electricity_kwh") is None,
        "unit_manual_review": False, "has_work_scope_text": False})
    row.update({"category_type": "UNKNOWN", "collection_name": "UNKNOWN", "department_name": "UNKNOWN",
                "department_type": "UNKNOWN", "section_name": "UNKNOWN",
                "masterformat_division": div if div != "GLOBAL" else "UNKNOWN",
                "base_unit": str(unit).strip().lower(), "unit_dimension": _dimension(unit)})
    X = pd.DataFrame([row])
    for c in BOOL:
        X[c] = X[c].astype(int)

    # --- EXACT training text order: name + section_title + subsection + resources + scope ---
    text = f"{description}   {composition.get('resource_names', '')} "
    Xn = csr_matrix(X[pre["num_bool_cols"]].astype(float).values)
    Xc = pre["onehot"].transform(X[pre["cat_cols"]].astype(str))
    Xt = pre["tfidf"].transform([text])
    pred_log = float(assets.model().predict(hstack([Xn, Xc, Xt]).tocsr())[0])
    live_price = max(float(np.expm1(pred_log)), 1e-6)

    ver = assets.versions()
    lo, hi = live_price * ver["interval_ratio_lo"], live_price * ver["interval_ratio_hi"]
    conf, reason = _confidence(False, has_comp, best["score"])
    return {
        "expected_benchmark_unit_price": live_price,
        "interval_low": min(lo, live_price), "interval_high": max(hi, live_price),
        "base_date": ver["ddc_base_date"], "division_used": div,
        "confidence": conf, "confidence_reason": reason,
        "imputation_note": ("division-median imputation for missing composition features"
                            if not has_comp else "user-provided composition used"),
        "ddc_matches": ddc, "ddc_best_score": best["score"],
        "retrieval_reference": {  # validated per-item numbers for the nearest catalog item (cross-check)
            "name": best["rate_final_name"], "price": best["predicted_base_unit_price"],
            "interval": [best["interval_low"], best["interval_high"]], "score": best["score"]},
    }
