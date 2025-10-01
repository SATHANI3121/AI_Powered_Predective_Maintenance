"""
Pydantic schemas for API request/response models
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class SeverityLevel(str, Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SensorType(str, Enum):
    """Sensor types"""
    VIBRATION = "vibration"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    RPM = "rpm"
    CURRENT = "current"
    VOLTAGE = "voltage"


# Base schemas
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Data ingestion schemas
class SensorReading(BaseModel):
    """Individual sensor reading"""
    timestamp: datetime
    machine_id: str = Field(..., min_length=1, max_length=50)
    sensor: SensorType
    value: float = Field(..., ge=-1000, le=10000)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UploadResult(BaseResponse):
    """Result of CSV upload"""
    rows_ingested: int = Field(..., ge=0)
    file_size_bytes: int = Field(..., ge=0)
    processing_time_seconds: float = Field(..., ge=0)


# Prediction schemas
class PredictRequest(BaseModel):
    """Request for failure prediction"""
    machine_id: str = Field(..., min_length=1, max_length=50)
    horizon_hours: int = Field(24, ge=1, le=168)  # 1 hour to 1 week
    include_anomaly: bool = True
    include_factors: bool = True


class PredictionRecord(BaseModel):
    """Individual prediction record"""
    timestamp: datetime
    machine_id: str
    horizon_hours: int
    failure_probability: float = Field(..., ge=0, le=1)
    anomaly_score: Optional[float] = Field(None, ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    top_factors: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PredictResponse(BaseResponse):
    """Response for failure prediction"""
    predictions: List[PredictionRecord]
    model_version: str
    prediction_time: datetime = Field(default_factory=datetime.utcnow)


# Alert schemas
class Alert(BaseModel):
    """Alert model"""
    id: int
    created_at: datetime
    machine_id: str
    severity: SeverityLevel
    message: str
    failure_probability: Optional[float] = None
    anomaly_score: Optional[float] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertResponse(BaseResponse):
    """Response for alerts"""
    alerts: List[Alert]
    total_count: int
    unresolved_count: int


class CreateAlertRequest(BaseModel):
    """Request to create an alert"""
    machine_id: str = Field(..., min_length=1, max_length=50)
    severity: SeverityLevel
    message: str = Field(..., min_length=1, max_length=500)
    failure_probability: Optional[float] = Field(None, ge=0, le=1)
    anomaly_score: Optional[float] = Field(None, ge=0, le=1)


# Chat schemas
class ChatRequest(BaseModel):
    """Request for chat/RAG query"""
    question: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = None
    include_sources: bool = True
    max_results: int = Field(5, ge=1, le=20)


class ChatSource(BaseModel):
    """Source document for chat response"""
    title: str
    page: Optional[int] = None
    relevance_score: float = Field(..., ge=0, le=1)
    content: str


class ChatResponse(BaseResponse):
    """Response for chat query"""
    answer: str
    sources: Optional[List[ChatSource]] = None
    confidence: float = Field(..., ge=0, le=1)
    processing_time_seconds: float = Field(..., ge=0)


# Machine schemas
class Machine(BaseModel):
    """Machine information"""
    id: int
    machine_id: str
    name: Optional[str] = None
    line: Optional[str] = None
    criticality: int = Field(..., ge=1, le=5)
    status: str = "active"
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MachineResponse(BaseResponse):
    """Response for machine information"""
    machines: List[Machine]
    total_count: int


# Analytics schemas
class AnalyticsRequest(BaseModel):
    """Request for analytics data"""
    machine_id: Optional[str] = None
    start_date: datetime
    end_date: datetime
    metrics: List[str] = Field(default=["failure_probability", "anomaly_score"])
    aggregation: str = Field("hour", regex="^(minute|hour|day|week)$")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class AnalyticsDataPoint(BaseModel):
    """Analytics data point"""
    timestamp: datetime
    machine_id: str
    metrics: Dict[str, float]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsResponse(BaseResponse):
    """Response for analytics data"""
    data: List[AnalyticsDataPoint]
    total_points: int
    date_range: Dict[str, datetime]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Error schemas
class ErrorDetail(BaseModel):
    """Error detail"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# File upload schemas
class FileUploadResponse(BaseResponse):
    """Response for file upload"""
    filename: str
    content_type: str
    size_bytes: int
    rows_processed: int
    validation_errors: Optional[List[str]] = None


# Model performance schemas
class ModelMetrics(BaseModel):
    """Model performance metrics"""
    model_name: str
    version: str
    precision: float = Field(..., ge=0, le=1)
    recall: float = Field(..., ge=0, le=1)
    f1_score: float = Field(..., ge=0, le=1)
    accuracy: float = Field(..., ge=0, le=1)
    auc_roc: float = Field(..., ge=0, le=1)
    last_trained: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ModelMetricsResponse(BaseResponse):
    """Response for model metrics"""
    metrics: List[ModelMetrics]
    best_model: Optional[str] = None


