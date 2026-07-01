# -*- coding: utf-8 -*-
"""UAE mode = the SAME validated US→Dubai regional calibration (benchmark→benchmark).
Output is a region-calibrated benchmark estimate — NOT a confirmed contractor market price."""
from . import assets

USD_AED = 3.6725  # UAE Central Bank fixed peg
DIM_FACTOR = {"volume": 1.30795, "area": 10.7639, "length": 3.28084, "weight": 1.10231,
              "count": 1.0, "lumpsum": 1.0, "time": 1.0, "unknown": 1.0}
DIM_METRIC_UNIT = {"volume": "m3", "area": "m2", "length": "m", "weight": "tonne",
                   "count": "ea", "lumpsum": "LS", "time": "unit", "unknown": "unit"}
CAVEAT = ("This is a region-calibrated BENCHMARK estimate (US benchmark → unit/FX conversion → "
          "Dubai calibration factor). It is NOT a confirmed UAE contractor market price.")


def to_uae(price_usd: float, unit_dimension: str, division: str = None):
    fac = assets.dubai_factors()
    row = fac[fac.us_division == division] if division else fac.iloc[0:0]
    n = int(row["n"].iloc[0]) if len(row) else 0
    if len(row) and n >= 30:
        cf, level = float(row["calibration_factor"].iloc[0]), f"division ({division}, n={n})"
    else:
        g = fac[fac.us_division == "GLOBAL"]
        cf, level = float(g["calibration_factor"].iloc[0]), "global (median Dubai/US ratio)"
    ucf = DIM_FACTOR.get(unit_dimension, 1.0)
    aed = price_usd * ucf * USD_AED * cf
    return {"expected_benchmark_price_aed": max(aed, 1e-6),
            "aed_unit": DIM_METRIC_UNIT.get(unit_dimension, "unit"),
            "unit_conversion_factor": ucf, "fx_usd_aed": USD_AED,
            "calibration_factor": cf, "calibration_level": level, "caveat": CAVEAT}
