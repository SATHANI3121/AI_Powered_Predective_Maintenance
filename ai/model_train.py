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

from ai.features import build_features


def _heuristic_label(feats: pd.DataFrame) -> pd.Series:
    """
    Create heuristic labels based on high temperature and vibration values.
    Uses percentile-based thresholds to adapt to the data distribution.
    """
    temp_cols = [c for c in feats.columns if c.startswith("temperature_roll") and c.endswith("_mean")]
    vib_cols = [c for c in feats.columns if c.startswith("vibration_roll") and c.endswith("_mean")]
    
    if not temp_cols or not vib_cols:
        # If no rolling features, try to create labels from raw max values
        return pd.Series([0] * len(feats), index=feats.index)
    
    # Get max values across rolling windows
    temp_max = feats[temp_cols].max(axis=1)
    vib_max = feats[vib_cols].max(axis=1)
    
    # Use adaptive thresholds based on 90th percentile
    temp_threshold = max(temp_max.quantile(0.90), 75)  # At least 75°F
    vib_threshold = max(vib_max.quantile(0.90), 0.25)  # At least 0.25
    
    # Label as failure if BOTH temperature and vibration are high
    y = ((temp_max > temp_threshold) & (vib_max > vib_threshold)).astype(int)
    
    # Ensure we have at least some positive examples (top 5%)
    if y.sum() == 0:
        # Use combined score approach
        temp_norm = (temp_max - temp_max.min()) / (temp_max.max() - temp_max.min() + 1e-9)
        vib_norm = (vib_max - vib_max.min()) / (vib_max.max() - vib_max.min() + 1e-9)
        combined_score = temp_norm * 0.6 + vib_norm * 0.4
        threshold = combined_score.quantile(0.95)
        y = (combined_score > threshold).astype(int)
    
    return y


def train_models(data_csv: str, out_dir: str = "ai/artifacts") -> Tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)

    print(f"📊 Loading data from {data_csv}...")
    raw = pd.read_csv(data_csv, parse_dates=["timestamp"])
    print(f"   Loaded {len(raw)} sensor readings")
    
    print("🔧 Building features...")
    feats = build_features(raw)

    if feats.empty:
        raise ValueError("No features generated. Check input data frequency and coverage.")

    print(f"   Generated {len(feats)} feature rows with {len(feats.columns)} columns")
    
    X = feats.drop(columns=["timestamp", "machine_id"], errors="ignore")
    y = _heuristic_label(feats)
    
    print(f"📈 Labels: {y.sum()} failures out of {len(y)} samples ({100*y.mean():.1f}%)")

    print("🤖 Training XGBoost classifier...")
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
    print("   ✅ XGBoost training complete")

    print("🔍 Training Isolation Forest...")
    iso = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
    iso.fit(X)
    print("   ✅ Isolation Forest training complete")

    clf_path = os.path.join(out_dir, "failure_clf.joblib")
    if_path = os.path.join(out_dir, "anomaly_if.joblib")
    
    print(f"💾 Saving models to {out_dir}...")
    joblib.dump({"model": clf, "feature_cols": list(X.columns)}, clf_path)
    joblib.dump({"model": iso, "feature_cols": list(X.columns)}, if_path)
    
    print(f"✨ Training complete!")
    print(f"   Failure model: {clf_path}")
    print(f"   Anomaly model: {if_path}")
    
    return clf_path, if_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="ai/artifacts")
    args = ap.parse_args()
    train_models(args.data, args.out)


if __name__ == "__main__":
    main()


