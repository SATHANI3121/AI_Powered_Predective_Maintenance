"""
Database session management and helper functions
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, Machine, SensorReading, Prediction, Alert


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:pass@localhost:5432/pdm")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    return SessionLocal()


def insert_sensor_data(db: Session, df: pd.DataFrame) -> int:
    rows = 0
    # Ensure machines exist
    machine_ids = df["machine_id"].unique().tolist()
    existing = {m.machine_id for m in db.query(Machine).filter(Machine.machine_id.in_(machine_ids)).all()}
    for mid in machine_ids:
        if mid not in existing:
            db.add(Machine(machine_id=mid, line="unknown", criticality=3))
    db.commit()

    for _, row in df.iterrows():
        db.add(
            SensorReading(
                machine_id=row["machine_id"],
                ts=pd.to_datetime(row["timestamp"]).to_pydatetime(),
                sensor=str(row["sensor"]),
                value=float(row["value"]),
            )
        )
        rows += 1
    db.commit()
    return rows


def get_machine_by_id(db: Session, machine_id: str):
    return db.query(Machine).filter(Machine.machine_id == machine_id).first()


def get_recent_sensor_data(db: Session, machine_id: str, hours: int = 48) -> pd.DataFrame:
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        db.query(SensorReading)
        .filter(SensorReading.machine_id == machine_id, SensorReading.ts >= since)
        .order_by(SensorReading.ts.asc())
        .all()
    )
    if not rows:
        return pd.DataFrame(columns=["timestamp", "machine_id", "sensor", "value"])  
    data = [
        {
            "timestamp": r.ts,
            "machine_id": r.machine_id,
            "sensor": r.sensor,
            "value": r.value,
        }
        for r in rows
    ]
    return pd.DataFrame(data)


def store_predictions(db: Session, machine_id: str, df: pd.DataFrame, model_version: str = "1.0.0") -> int:
    rows = 0
    for _, row in df.iterrows():
        db.add(
            Prediction(
                machine_id=machine_id,
                ts=pd.to_datetime(row["timestamp"]).to_pydatetime(),
                horizon_hours=int(row.get("horizon_hours", 24)),
                failure_prob=float(row["failure_prob_24h"]),
                anomaly_score=float(row.get("anomaly_score", 0.0)),
                top_factors=row.get("top_factors"),
                model_version=model_version,
            )
        )
        rows += 1
    db.commit()
    return rows


def get_recent_predictions(db: Session, hours: int = 24) -> List[Prediction]:
    since = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(Prediction)
        .filter(Prediction.ts >= since)
        .order_by(Prediction.ts.desc())
        .all()
    )


def create_alert(
    db: Session,
    machine_id: str,
    severity: str,
    message: str,
    failure_probability: float | None = None,
    anomaly_score: float | None = None,
) -> Alert:
    alert = Alert(
        machine_id=machine_id,
        severity=severity,
        message=message,
        failure_probability=failure_probability,
        anomaly_score=anomaly_score,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_alerts(
    db: Session,
    machine_id: str | None = None,
    severity: str | None = None,
    resolved: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Alert]:
    q = db.query(Alert)
    if machine_id:
        q = q.filter(Alert.machine_id == machine_id)
    if severity:
        q = q.filter(Alert.severity == severity)
    if resolved is not None:
        q = q.filter(Alert.resolved == resolved)
    return q.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()


def get_alert_by_id(db: Session, alert_id: int) -> Alert | None:
    return db.query(Alert).filter(Alert.id == alert_id).first()


def update_alert(db: Session, alert_id: int, resolved: bool = True) -> Alert:
    alert = get_alert_by_id(db, alert_id)
    if not alert:
        raise ValueError("Alert not found")
    alert.resolved = resolved
    alert.resolved_at = datetime.utcnow() if resolved else None
    db.commit()
    db.refresh(alert)
    return alert


def fetch_recent_for_all_machines(db: Session, hours: int = 48) -> Dict[str, pd.DataFrame]:
    machine_ids = [m.machine_id for m in db.query(Machine.machine_id).all()]
    return {mid: get_recent_sensor_data(db, mid, hours=hours) for mid in machine_ids}


