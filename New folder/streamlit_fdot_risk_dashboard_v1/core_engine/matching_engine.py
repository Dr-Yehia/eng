# -*- coding: utf-8 -*-
"""Semantic matching to the DDC catalog + FDOT historical item lookup.
Same TF-IDF cosine approach used (and validated as supporting-only) in the risk packages."""
import re
from functools import lru_cache
import numpy as np
from . import assets

STRONG, CANDIDATE = 0.85, 0.50


@lru_cache(maxsize=1)
def _vectorizer():
    from sklearn.feature_extraction.text import TfidfVectorizer
    corpus = assets.catalog()["rate_final_name"].astype(str).tolist()
    vec = TfidfVectorizer(min_df=1, ngram_range=(1, 2), stop_words="english").fit(corpus)
    return vec, vec.transform(corpus)


def match_ddc(description: str, top_k: int = 3):
    """Return top-k catalog matches: list of dicts with score + validated predicted price/interval."""
    from sklearn.metrics.pairwise import cosine_similarity
    vec, D = _vectorizer()
    sims = cosine_similarity(vec.transform([str(description)]), D)[0]
    order = np.argsort(sims)[::-1][:top_k]
    cat = assets.catalog()
    out = []
    for i in order:
        r = cat.iloc[int(i)]
        s = float(sims[int(i)])
        out.append({"rate_code": r["rate_code"], "rate_final_name": r["rate_final_name"],
                    "masterformat_division": r["masterformat_division"], "base_unit": r["base_unit"],
                    "unit_dimension": r["unit_dimension"], "score": s,
                    "match_status": "strong" if s >= STRONG else ("candidate_review" if s >= CANDIDATE else "no_match"),
                    "predicted_base_unit_price": float(r["predicted_base_unit_price"]),
                    "interval_low": float(r["prediction_interval_low"]),
                    "interval_high": float(r["prediction_interval_high"])})
    return out


def norm_item_id(item_id: str) -> str:
    return re.sub(r"\s+", "", str(item_id)).upper()


def match_fdot_historical(item_id: str, unit: str):
    """FDOT 2024 statewide weighted-average lookup by item number + unit compatibility."""
    if not item_id or not str(item_id).strip():
        return None
    H = assets.fdot_historical()
    key = norm_item_id(item_id)
    if key not in H.index:
        return {"status": "no_match", "wavg": None, "hunit": None}
    row = H.loc[key]
    unit_ok = str(unit).strip().upper() == str(row["hunit"]).strip().upper()
    return {"status": "matched" if unit_ok else "unit_mismatch",
            "wavg": float(row["wavg"]) if unit_ok else None, "hunit": str(row["hunit"])}
