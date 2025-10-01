"""
SQLAlchemy models for Predictive Maintenance Platform
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True)
    machine_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    line = Column(String(100), nullable=True)
    criticality = Column(Integer, nullable=False, default=3)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    readings = relationship("SensorReading", back_populates="machine", cascade="all,delete-orphan")
    predictions = relationship("Prediction", back_populates="machine", cascade="all,delete-orphan")
    alerts = relationship("Alert", back_populates="machine", cascade="all,delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True)
    machine_id = Column(String(50), ForeignKey("machines.machine_id"), index=True, nullable=False)
    ts = Column(DateTime, index=True, nullable=False)
    sensor = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    machine = relationship("Machine", back_populates="readings")

    __table_args__ = (
        Index("ix_sensor_readings_machine_ts", "machine_id", "ts"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True)
    machine_id = Column(String(50), ForeignKey("machines.machine_id"), index=True, nullable=False)
    ts = Column(DateTime, index=True, nullable=False)
    horizon_hours = Column(Integer, nullable=False, default=24)
    failure_prob = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=True)
    top_factors = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    machine = relationship("Machine", back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_machine_ts", "machine_id", "ts"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    machine_id = Column(String(50), ForeignKey("machines.machine_id"), index=True, nullable=False)
    severity = Column(String(16), nullable=False)  # LOW/MEDIUM/HIGH/CRITICAL
    message = Column(String(500), nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    failure_probability = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)

    machine = relationship("Machine", back_populates="alerts")


