# -*- coding: utf-8 -*-
"""Official standardized input template (I/O) + result report builder (Excel/CSV/JSON).
The template is how new cases enter the system — no automatic PDF parsing is promised."""
import io, json
import numpy as np, pandas as pd
from . import assets, audit_logger


def build_template(n_bidders: int = 4) -> bytes:
    """Return an .xlsx with an Instructions sheet + a ready-to-fill Bid-Tab template (N bidder columns)."""
    cols = ["line_no", "item_id", "description", "section_name", "unit", "quantity", "is_lump_sum", "target_date"]
    bcols = [f"bidder{i}_unit_price" for i in range(1, n_bidders + 1)]
    example = {"line_no": "0130", "item_id": "0327 70 2", "description": "Milling existing asphalt pavement, 1.5 in",
               "section_name": "Roadway", "unit": "SY", "quantity": 64672, "is_lump_sum": False,
               "target_date": "2026-05-01", "bidder1_unit_price": 4.65, "bidder2_unit_price": 3.60,
               "bidder3_unit_price": 4.20, "bidder4_unit_price": 5.10}
    tmpl = pd.DataFrame([{c: example.get(c, "") for c in cols + bcols}])
    instr = pd.DataFrame({
        "field": cols + bcols + ["(single-price alt.)"],
        "required": (["yes", "recommended", "yes", "optional", "yes", "yes", "auto", "yes"]
                     + ["at least one bidder price"] * n_bidders + ["actual_unit_price (if no bidders)"]),
        "meaning": [
            "bid line number", "FDOT pay item number — UNLOCKS the official historical benchmark",
            "item description (used for the ML benchmark)", "project section (Roadway/Signing/…)",
            "unit of measure (SY, TN, LF, EA, CY, LS…)", "bid quantity", "TRUE for lump-sum items",
            "pricing date for time escalation (YYYY-MM-DD)"]
        + ["unit price offered by bidder i; bidder1 = winner (lowest total)"] * n_bidders
        + ["use ONE actual_unit_price column instead of bidder columns if you only have the awarded price"],
    })
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        instr.to_excel(xw, "Instructions", index=False)
        tmpl.to_excel(xw, "BidTab_Input", index=False)
        pd.DataFrame({"note": [
            "1) Fill BidTab_Input (one row per pay item). Keep column names unchanged.",
            "2) bidder1 = winning bidder. Add/remove bidderN_unit_price columns as needed.",
            "3) If you only have the awarded price, delete bidder columns and add 'actual_unit_price'.",
            "4) item_id + matching unit lets the system use the official FDOT 2024 historical benchmark.",
            "5) Upload the filled file back into the dashboard -> Validation -> Run.",
            "This tool reports ABNORMAL PRICING RISK for commercial review — not fraud."]}).to_excel(xw, "README", index=False)
    return buf.getvalue()


DISPLAY = ["line_no", "item_id", "description", "section_name", "unit", "quantity", "is_lump_sum",
           "actual_unit_price", "non_winner_median", "deviation_vs_market",
           "historical_benchmark", "deviation_vs_historical", "historical_match_status",
           "market_risk_flag", "historical_risk_flag", "combined_risk_flag", "risk_direction",
           "evidence_class", "risk_confidence", "overpricing_exposure", "data_quality_flag", "recommended_action"]


def result_csv(res: pd.DataFrame) -> bytes:
    cols = [c for c in DISPLAY if c in res.columns]
    return res[cols].to_csv(index=False).encode()


def result_json(res: pd.DataFrame, summary: dict, case_id: str) -> bytes:
    cols = [c for c in DISPLAY if c in res.columns]
    payload = {"case_id": case_id, "engine_versions": audit_logger.versions(),
               "summary": {k: (v if not isinstance(v, dict) else v) for k, v in summary.items() if k != "thresholds"},
               "items": json.loads(res[cols].to_json(orient="records"))}
    return json.dumps(payload, indent=2, default=str).encode()


def result_excel(res: pd.DataFrame, summary: dict, case_id: str) -> bytes:
    cols = [c for c in DISPLAY if c in res.columns]
    ELEV = {"High", "Critical"}
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        pd.DataFrame([{"field": "case_id", "value": case_id},
                      {"field": "generated_at", "value": pd.Timestamp.now().isoformat()},
                      *[{"field": k, "value": (json.dumps(v) if isinstance(v, dict) else v)}
                        for k, v in summary.items() if k != "thresholds"],
                      {"field": "wording", "value": "abnormal pricing risk / commercial review — not fraud"}]
                     ).to_excel(xw, "01_Summary", index=False)
        res[cols].to_excel(xw, "02_Item_Level_Risk", index=False)
        res[res.evidence_class == "confirmed_by_both"][cols].to_excel(xw, "03_Confirmed_By_Both", index=False)
        res[res.combined_risk_flag.isin(ELEV)].nlargest(50, "overpricing_exposure")[cols].to_excel(xw, "04_Top_Exposure", index=False)
        res[res.is_lump_sum][cols].to_excel(xw, "05_Lump_Sum_Items", index=False)
        pd.DataFrame([{"component": k, "version": str(v)} for k, v in audit_logger.versions().items()]).to_excel(xw, "06_Engine_Audit", index=False)
        if "thresholds" in summary:
            pd.DataFrame([{"benchmark": b, **{m: round(x, 2) for m, x in d.items()}}
                          for b, d in summary["thresholds"].items()]).to_excel(xw, "07_Statistical_Thresholds", index=False)
    return buf.getvalue()
