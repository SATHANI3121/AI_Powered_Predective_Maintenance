"""
Model inference utilities
"""

from __future__ import annotations

import os
from typing import Dict, Any, List

import joblib
import pandas as pd

from .features import build_features


class MLService:
    def __init__(self, artifacts_dir: str = "ai/artifacts"):
        self.artifacts_dir = artifacts_dir
        self._clf = joblib.load(os.path.join(artifacts_dir, "failure_clf.joblib"))
        self._iso = joblib.load(os.path.join(artifacts_dir, "anomaly_if.joblib"))

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        feats = build_features(df).sort_values("timestamp")
        return feats

    def predict_failure_probability(self, df: pd.DataFrame, horizon_hours: int = 24) -> float:
        feats = self._prepare(df)
        X = feats[self._clf["feature_cols"]]
        p = self._clf["model"].predict_proba(X)[:, 1]
        return float(p.iloc[-1]) if hasattr(p, "iloc") else float(p[-1])

    def detect_anomaly(self, df: pd.DataFrame) -> float:
        feats = self._prepare(df)
        X = feats[self._iso["feature_cols"]]
        a = -self._iso["model"].score_samples(X)
        # Normalize
        a_min, a_max = float(a.min()), float(a.max())
        score = (a[-1] - a_min) / (a_max - a_min + 1e-9)
        return float(score)

    def get_feature_importance(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        feats = self._prepare(df)
        X = feats[self._clf["feature_cols"]]
        importances = self._clf["model"].feature_importances_
        pairs = sorted(zip(X.columns, importances), key=lambda x: x[1], reverse=True)[:10]
        return [{"feature": f, "importance": float(val)} for f, val in pairs]

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "failure_model_version": "1.0.0",
            "anomaly_model_version": "1.0.0",
        }


