"""
Train XGBoost failure prediction and Isolation Forest anomaly detection models
"""

from __future__ import annotations

import argparse
import os
from typing import Tuple

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier

from .features import build_features


def _heuristic_label(feats: pd.DataFrame) -> pd.Series:
    temp_cols = [c for c in feats.columns if c.startswith("temperature_roll") and c.endswith("_mean")]
    vib_cols = [c for c in feats.columns if c.startswith("vibration_roll") and c.endswith("_mean")]
    if not temp_cols or not vib_cols:
        return pd.Series([0] * len(feats), index=feats.index)
    y = ((feats[temp_cols].max(axis=1) > 65) & (feats[vib_cols].max(axis=1) > 0.8)).astype(int)
    return y


def train_models(data_csv: str, out_dir: str = "ai/artifacts") -> Tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)

    raw = pd.read_csv(data_csv, parse_dates=["timestamp"])
    feats = build_features(raw)

    if feats.empty:
        raise ValueError("No features generated. Check input data frequency and coverage.")

    X = feats.drop(columns=["timestamp", "machine_id"], errors="ignore")
    y = _heuristic_label(feats)

    clf = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.07,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        n_jobs=4,
    )
    clf.fit(X, y)

    iso = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
    iso.fit(X)

    clf_path = os.path.join(out_dir, "failure_clf.joblib")
    if_path = os.path.join(out_dir, "anomaly_if.joblib")
    joblib.dump({"model": clf, "feature_cols": list(X.columns)}, clf_path)
    joblib.dump({"model": iso, "feature_cols": list(X.columns)}, if_path)
    return clf_path, if_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="ai/artifacts")
    args = ap.parse_args()
    train_models(args.data, args.out)


if __name__ == "__main__":
    main()


