"""
Feature engineering for time-series sensor data
Tall format input: timestamp, machine_id, sensor, value
"""

from __future__ import annotations

from typing import Iterable, Tuple
import pandas as pd


def build_features(
    df: pd.DataFrame,
    lags: Iterable[int] = (1, 2, 3, 6, 12),
    rolls: Iterable[int] = (3, 6, 12),
) -> pd.DataFrame:
    """Pivot tall data to wide and add lag/rolling stats per sensor.

    Args:
        df: DataFrame with columns timestamp, machine_id, sensor, value
        lags: lag windows in periods (assumes uniform sampling)
        rolls: rolling windows in periods

    Returns:
        Feature DataFrame with engineered columns and original keys
    """
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "machine_id"]).copy()

    data = df.copy()
    data = data.sort_values(["timestamp", "machine_id"])  # ensure order

    pivot = (
        data.pivot_table(
            index=["timestamp", "machine_id"],
            columns="sensor",
            values="value",
            aggfunc="mean",
        )
        .sort_index()
    )

    feat = pivot.copy()
    for col in pivot.columns:
        series = pivot[col]
        for L in lags:
            feat[f"{col}_lag{L}"] = series.shift(L)
        for R in rolls:
            feat[f"{col}_roll{R}_mean"] = series.rolling(R).mean()
            feat[f"{col}_roll{R}_std"] = series.rolling(R).std()

    feat = feat.dropna()
    feat = feat.reset_index()
    return feat


