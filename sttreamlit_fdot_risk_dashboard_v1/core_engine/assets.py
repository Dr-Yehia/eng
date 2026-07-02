# -*- coding: utf-8 -*-
"""Cached loaders for frozen validated assets. UI-independent (lru_cache, not st.cache)."""
import os, json, pickle
from functools import lru_cache
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
AST = os.path.join(HERE, "assets_data")
def _p(name): return os.path.join(AST, name)


@lru_cache(maxsize=1)
def versions():
    return json.load(open(_p("engine_versions.json"), encoding="utf-8"))


@lru_cache(maxsize=1)
def catalog():
    return pd.read_parquet(_p("ddc_catalog_predictions.parquet"))


@lru_cache(maxsize=1)
def pipeline():
    with open(_p("final_preprocessing_pipeline.pkl"), "rb") as f:
        return pickle.load(f)


@lru_cache(maxsize=1)
def model():
    import xgboost as xgb
    m = xgb.XGBRegressor()
    m.load_model(_p("final_xgboost_global_model.json"))
    return m


@lru_cache(maxsize=1)
def indices():
    df = pd.read_csv(_p("indices_snapshot.csv"))
    df["date"] = pd.to_datetime(df["date"])
    return df


@lru_cache(maxsize=1)
def fdot_historical():
    return pd.read_parquet(_p("fdot_historical_2024.parquet")).set_index("key")


@lru_cache(maxsize=1)
def dubai_factors():
    return pd.read_parquet(_p("dubai_calibration_factors.parquet"))


@lru_cache(maxsize=1)
def division_defaults():
    return pd.read_parquet(_p("division_feature_defaults.parquet")).set_index("masterformat_division")


@lru_cache(maxsize=1)
def feature_schema():
    return json.load(open(_p("feature_schema.json"), encoding="utf-8"))


@lru_cache(maxsize=1)
def risk_thresholds():
    return json.load(open(_p("risk_thresholds.json"), encoding="utf-8"))
