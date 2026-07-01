# -*- coding: utf-8 -*-
"""Audit trail: every engine run is stamped with all component versions (Q1 reproducibility)."""
import pandas as pd
from . import assets

_RUNS = []


def versions():
    v = assets.versions()
    return {k: v[k] for k in ["engine_version", "model_version", "data_version", "index_version",
                              "calibration_version", "risk_threshold_version", "parser_version",
                              "ddc_base_date", "wording_policy"]}


def log_run(mode: str, inputs: dict, outputs: dict):
    rec = {"timestamp": pd.Timestamp.now().isoformat(), "mode": mode,
           "inputs": inputs, "key_outputs": outputs, "versions": versions()}
    _RUNS.append(rec)
    return rec


def runs_df():
    if not _RUNS:
        return pd.DataFrame()
    rows = []
    for r in _RUNS:
        rows.append({"timestamp": r["timestamp"], "mode": r["mode"],
                     **{f"in_{k}": v for k, v in list(r["inputs"].items())[:6]},
                     **{f"out_{k}": v for k, v in list(r["key_outputs"].items())[:6]}})
    return pd.DataFrame(rows)
