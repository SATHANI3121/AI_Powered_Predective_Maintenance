"""
Prediction endpoints for failure risk and anomaly detection
"""

import logging
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.schemas import (
    PredictRequest, PredictResponse, PredictionRecord, 
    AnalyticsRequest, AnalyticsResponse, AnalyticsDataPoint
)
from api.deps import get_database, verify_api_key, get_ml_service, get_metrics_collector
from api.telemetry import structured_logger, PREDICTION_COUNT, PREDICTION_DURATION
from persistence.db import get_recent_sensor_data, get_machine_by_id
from ai.model_infer import MLService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict", response_model=PredictResponse, tags=["prediction"])
async def predict_failure_risk(
    request: PredictRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database),
    ml_service: MLService = Depends(get_ml_service),
    metrics_collector = Depends(get_metrics_collector)
):
    """
    Predict failure risk for a machine
    
    - **machine_id**: Machine identifier
    - **horizon_hours**: Prediction horizon (1-168 hours)
    - **include_anomaly**: Include anomaly detection
    - **include_factors**: Include feature importance
    """
    start_time = time.time()
    
    try:
        # Validate machine exists
        machine = get_machine_by_id(db, request.machine_id)
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine {request.machine_id} not found"
            )
        
        # Get recent sensor data
        sensor_data = get_recent_sensor_data(
            db, 
            request.machine_id, 
            hours=48  # Use last 48 hours for prediction
        )
        
        if sensor_data.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No sensor data available for machine {request.machine_id}"
            )
        
        # Make predictions
        predictions = []
        
        # Generate predictions for multiple time horizons if requested
        horizons = [request.horizon_hours]
        if request.horizon_hours == 24:
            horizons = [24, 48, 72]  # Default to multiple horizons
        
        for horizon in horizons:
            try:
                # Get failure probability
                failure_prob = ml_service.predict_failure_probability(
                    sensor_data, 
                    horizon_hours=horizon
                )
                
                # Get anomaly score if requested
                anomaly_score = None
                if request.include_anomaly:
                    anomaly_score = ml_service.detect_anomaly(sensor_data)
                
                # Get feature importance if requested
                top_factors = None
                if request.include_factors:
                    top_factors = ml_service.get_feature_importance(sensor_data)
                
                # Calculate confidence based on data quality and recency
                confidence = _calculate_confidence(sensor_data, horizon)
                
                prediction = PredictionRecord(
                    timestamp=sensor_data['timestamp'].max(),
                    machine_id=request.machine_id,
                    horizon_hours=horizon,
                    failure_probability=failure_prob,
                    anomaly_score=anomaly_score,
                    confidence=confidence,
                    top_factors=top_factors
                )
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Prediction error for horizon {horizon}: {e}")
                # Continue with other horizons
                continue
        
        if not predictions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate predictions"
            )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Record metrics
        for prediction in predictions:
            metrics_collector.record_prediction(
                model_type="failure_prediction",
                machine_id=request.machine_id,
                duration=processing_time
            )
        
        # Log structured data
        structured_logger.info(
            "Failure prediction completed",
            machine_id=request.machine_id,
            horizon_hours=request.horizon_hours,
            predictions_count=len(predictions),
            processing_time_seconds=processing_time,
            max_failure_prob=max(p.failure_probability for p in predictions),
            max_anomaly_score=max(p.anomaly_score for p in predictions if p.anomaly_score)
        )
        
        return PredictResponse(
            predictions=predictions,
            model_version="1.0.0",
            prediction_time=time.time()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during prediction"
        )


@router.get("/predict/batch", response_model=PredictResponse, tags=["prediction"])
async def predict_batch_failure_risk(
    machine_ids: List[str] = Query(..., description="List of machine IDs"),
    horizon_hours: int = Query(24, ge=1, le=168),
    include_anomaly: bool = Query(True),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database),
    ml_service: MLService = Depends(get_ml_service)
):
    """
    Predict failure risk for multiple machines
    
    - **machine_ids**: List of machine identifiers
    - **horizon_hours**: Prediction horizon
    - **include_anomaly**: Include anomaly detection
    """
    if len(machine_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 machines per batch request"
        )
    
    try:
        all_predictions = []
        
        for machine_id in machine_ids:
            try:
                # Get sensor data for machine
                sensor_data = get_recent_sensor_data(db, machine_id, hours=48)
                
                if sensor_data.empty:
                    logger.warning(f"No data for machine {machine_id}")
                    continue
                
                # Make prediction
                failure_prob = ml_service.predict_failure_probability(
                    sensor_data, 
                    horizon_hours=horizon_hours
                )
                
                anomaly_score = None
                if include_anomaly:
                    anomaly_score = ml_service.detect_anomaly(sensor_data)
                
                prediction = PredictionRecord(
                    timestamp=sensor_data['timestamp'].max(),
                    machine_id=machine_id,
                    horizon_hours=horizon_hours,
                    failure_probability=failure_prob,
                    anomaly_score=anomaly_score,
                    confidence=_calculate_confidence(sensor_data, horizon_hours)
                )
                
                all_predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Batch prediction error for {machine_id}: {e}")
                continue
        
        structured_logger.info(
            "Batch prediction completed",
            machine_count=len(machine_ids),
            successful_predictions=len(all_predictions),
            horizon_hours=horizon_hours
        )
        
        return PredictResponse(
            predictions=all_predictions,
            model_version="1.0.0",
            prediction_time=time.time()
        )
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during batch prediction"
        )


@router.get("/predict/analytics", response_model=AnalyticsResponse, tags=["prediction"])
async def get_prediction_analytics(
    request: AnalyticsRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database)
):
    """
    Get historical prediction analytics
    
    - **machine_id**: Optional machine filter
    - **start_date**: Start date for analytics
    - **end_date**: End date for analytics
    - **metrics**: Metrics to include
    - **aggregation**: Time aggregation level
    """
    try:
        # This would typically query a time-series database or analytics store
        # For now, return mock data
        analytics_data = []
        
        # Mock implementation - in production, this would query actual analytics
        import pandas as pd
        from datetime import timedelta
        
        current_time = request.start_date
        while current_time <= request.end_date:
            # Mock data point
            data_point = AnalyticsDataPoint(
                timestamp=current_time,
                machine_id=request.machine_id or "M01",
                metrics={
                    "failure_probability": 0.1 + (hash(str(current_time)) % 100) / 1000,
                    "anomaly_score": 0.05 + (hash(str(current_time)) % 50) / 1000
                }
            )
            analytics_data.append(data_point)
            
            # Increment based on aggregation
            if request.aggregation == "minute":
                current_time += timedelta(minutes=1)
            elif request.aggregation == "hour":
                current_time += timedelta(hours=1)
            elif request.aggregation == "day":
                current_time += timedelta(days=1)
            else:  # week
                current_time += timedelta(weeks=1)
        
        return AnalyticsResponse(
            data=analytics_data,
            total_points=len(analytics_data),
            date_range={
                "start": request.start_date,
                "end": request.end_date
            }
        )
        
    except Exception as e:
        logger.error(f"Analytics error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during analytics query"
        )


@router.get("/predict/models/status", tags=["prediction"])
async def get_model_status(
    api_key: str = Depends(verify_api_key),
    ml_service: MLService = Depends(get_ml_service)
):
    """
    Get status of ML models
    
    Returns model versions, performance metrics, and training status
    """
    try:
        # Get model information
        model_info = ml_service.get_model_info()
        
        return {
            "models": {
                "failure_prediction": {
                    "version": model_info.get("failure_model_version", "1.0.0"),
                    "status": "loaded",
                    "last_trained": model_info.get("last_trained", "2024-01-01T00:00:00Z"),
                    "performance": {
                        "accuracy": model_info.get("accuracy", 0.85),
                        "precision": model_info.get("precision", 0.82),
                        "recall": model_info.get("recall", 0.88),
                        "f1_score": model_info.get("f1_score", 0.85)
                    }
                },
                "anomaly_detection": {
                    "version": model_info.get("anomaly_model_version", "1.0.0"),
                    "status": "loaded",
                    "last_trained": model_info.get("last_trained", "2024-01-01T00:00:00Z"),
                    "performance": {
                        "auc_roc": model_info.get("auc_roc", 0.92),
                        "contamination": model_info.get("contamination", 0.02)
                    }
                }
            },
            "training_status": {
                "last_training": "2024-01-01T03:00:00Z",
                "next_training": "2024-01-02T03:00:00Z",
                "training_frequency": "daily"
            }
        }
        
    except Exception as e:
        logger.error(f"Model status error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting model status"
        )


def _calculate_confidence(sensor_data, horizon_hours: int) -> float:
    """Calculate prediction confidence based on data quality"""
    try:
        # Base confidence
        confidence = 0.8
        
        # Adjust based on data recency
        latest_time = sensor_data['timestamp'].max()
        time_diff_hours = (pd.Timestamp.now() - latest_time).total_seconds() / 3600
        
        if time_diff_hours > 24:
            confidence -= 0.2
        elif time_diff_hours > 12:
            confidence -= 0.1
        
        # Adjust based on data completeness
        expected_sensors = ['vibration', 'temperature', 'pressure', 'rpm']
        available_sensors = sensor_data['sensor'].unique()
        sensor_coverage = len(set(available_sensors) & set(expected_sensors)) / len(expected_sensors)
        confidence *= sensor_coverage
        
        # Adjust based on prediction horizon
        if horizon_hours > 48:
            confidence *= 0.9
        elif horizon_hours > 24:
            confidence *= 0.95
        
        return max(0.1, min(1.0, confidence))
        
    except Exception:
        return 0.5  # Default confidence
