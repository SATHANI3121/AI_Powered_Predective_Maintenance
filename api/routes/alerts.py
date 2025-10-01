"""
Alert management endpoints
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.schemas import (
    Alert, AlertResponse, CreateAlertRequest, SeverityLevel
)
from api.deps import get_database, verify_api_key, get_metrics_collector
from api.telemetry import structured_logger, ALERT_COUNT
from persistence.db import (
    get_alerts, create_alert, update_alert, get_alert_by_id,
    get_machine_by_id, get_recent_predictions
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/alerts", response_model=AlertResponse, tags=["alerts"])
async def get_alerts(
    machine_id: Optional[str] = Query(None, description="Filter by machine ID"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database)
):
    """
    Get alerts with optional filtering
    
    - **machine_id**: Filter by specific machine
    - **severity**: Filter by severity level
    - **resolved**: Filter by resolution status
    - **limit**: Maximum number of alerts to return
    - **offset**: Number of alerts to skip
    """
    try:
        # Get alerts from database
        alerts_data = get_alerts(
            db,
            machine_id=machine_id,
            severity=severity.value if severity else None,
            resolved=resolved,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        alerts = []
        for alert_data in alerts_data:
            alert = Alert(
                id=alert_data.id,
                created_at=alert_data.created_at,
                machine_id=alert_data.machine_id,
                severity=SeverityLevel(alert_data.severity),
                message=alert_data.message,
                failure_probability=alert_data.failure_probability,
                anomaly_score=alert_data.anomaly_score,
                resolved=alert_data.resolved,
                resolved_at=alert_data.resolved_at
            )
            alerts.append(alert)
        
        # Count total and unresolved
        total_count = len(alerts)
        unresolved_count = len([a for a in alerts if not a.resolved])
        
        structured_logger.info(
            "Alerts retrieved",
            machine_id=machine_id,
            severity=severity.value if severity else None,
            resolved=resolved,
            total_count=total_count,
            unresolved_count=unresolved_count
        )
        
        return AlertResponse(
            alerts=alerts,
            total_count=total_count,
            unresolved_count=unresolved_count
        )
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting alerts"
        )


@router.post("/alerts", response_model=Alert, tags=["alerts"])
async def create_alert(
    request: CreateAlertRequest,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database),
    metrics_collector = Depends(get_metrics_collector)
):
    """
    Create a new alert
    
    - **machine_id**: Machine identifier
    - **severity**: Alert severity level
    - **message**: Alert message
    - **failure_probability**: Optional failure probability
    - **anomaly_score**: Optional anomaly score
    """
    try:
        # Validate machine exists
        machine = get_machine_by_id(db, request.machine_id)
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Machine {request.machine_id} not found"
            )
        
        # Create alert in database
        alert_data = create_alert(
            db,
            machine_id=request.machine_id,
            severity=request.severity.value,
            message=request.message,
            failure_probability=request.failure_probability,
            anomaly_score=request.anomaly_score
        )
        
        # Record metrics
        metrics_collector.record_alert(
            severity=request.severity.value,
            machine_id=request.machine_id
        )
        
        # Log structured data
        structured_logger.warning(
            "Alert created",
            alert_id=alert_data.id,
            machine_id=request.machine_id,
            severity=request.severity.value,
            message=request.message,
            failure_probability=request.failure_probability,
            anomaly_score=request.anomaly_score
        )
        
        return Alert(
            id=alert_data.id,
            created_at=alert_data.created_at,
            machine_id=alert_data.machine_id,
            severity=SeverityLevel(alert_data.severity),
            message=alert_data.message,
            failure_probability=alert_data.failure_probability,
            anomaly_score=alert_data.anomaly_score,
            resolved=alert_data.resolved,
            resolved_at=alert_data.resolved_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error creating alert"
        )


@router.put("/alerts/{alert_id}/resolve", response_model=Alert, tags=["alerts"])
async def resolve_alert(
    alert_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database)
):
    """
    Resolve an alert
    
    - **alert_id**: Alert identifier
    """
    try:
        # Get alert
        alert_data = get_alert_by_id(db, alert_id)
        if not alert_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )
        
        if alert_data.resolved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Alert {alert_id} is already resolved"
            )
        
        # Update alert
        updated_alert = update_alert(db, alert_id, resolved=True)
        
        structured_logger.info(
            "Alert resolved",
            alert_id=alert_id,
            machine_id=updated_alert.machine_id,
            severity=updated_alert.severity
        )
        
        return Alert(
            id=updated_alert.id,
            created_at=updated_alert.created_at,
            machine_id=updated_alert.machine_id,
            severity=SeverityLevel(updated_alert.severity),
            message=updated_alert.message,
            failure_probability=updated_alert.failure_probability,
            anomaly_score=updated_alert.anomaly_score,
            resolved=updated_alert.resolved,
            resolved_at=updated_alert.resolved_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error resolving alert"
        )


@router.get("/alerts/{alert_id}", response_model=Alert, tags=["alerts"])
async def get_alert(
    alert_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database)
):
    """
    Get a specific alert by ID
    
    - **alert_id**: Alert identifier
    """
    try:
        alert_data = get_alert_by_id(db, alert_id)
        if not alert_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )
        
        return Alert(
            id=alert_data.id,
            created_at=alert_data.created_at,
            machine_id=alert_data.machine_id,
            severity=SeverityLevel(alert_data.severity),
            message=alert_data.message,
            failure_probability=alert_data.failure_probability,
            anomaly_score=alert_data.anomaly_score,
            resolved=alert_data.resolved,
            resolved_at=alert_data.resolved_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting alert"
        )


@router.post("/alerts/auto-generate", tags=["alerts"])
async def auto_generate_alerts(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database),
    metrics_collector = Depends(get_metrics_collector)
):
    """
    Automatically generate alerts based on recent predictions
    
    This endpoint checks recent predictions and creates alerts for high-risk conditions
    """
    try:
        # Get recent predictions (last 24 hours)
        recent_predictions = get_recent_predictions(db, hours=24)
        
        alerts_created = 0
        
        for prediction in recent_predictions:
            # Check if alert should be created
            should_create_alert = False
            severity = SeverityLevel.LOW
            message = ""
            
            # High failure probability
            if prediction.failure_probability > 0.9:
                should_create_alert = True
                severity = SeverityLevel.CRITICAL
                message = f"CRITICAL: Machine {prediction.machine_id} has {prediction.failure_probability:.1%} failure probability in next {prediction.horizon_hours}h"
            elif prediction.failure_probability > 0.75:
                should_create_alert = True
                severity = SeverityLevel.HIGH
                message = f"HIGH: Machine {prediction.machine_id} has {prediction.failure_probability:.1%} failure probability in next {prediction.horizon_hours}h"
            elif prediction.failure_probability > 0.5:
                should_create_alert = True
                severity = SeverityLevel.MEDIUM
                message = f"MEDIUM: Machine {prediction.machine_id} has {prediction.failure_probability:.1%} failure probability in next {prediction.horizon_hours}h"
            
            # High anomaly score
            if prediction.anomaly_score and prediction.anomaly_score > 0.9:
                if not should_create_alert or severity == SeverityLevel.LOW:
                    should_create_alert = True
                    severity = SeverityLevel.HIGH
                    message = f"HIGH: Machine {prediction.machine_id} showing anomalous behavior (score: {prediction.anomaly_score:.2f})"
            
            if should_create_alert:
                # Check if alert already exists for this machine and time period
                existing_alerts = get_alerts(
                    db,
                    machine_id=prediction.machine_id,
                    severity=severity.value,
                    resolved=False,
                    limit=1
                )
                
                # Only create if no recent alert exists
                if not existing_alerts or (datetime.utcnow() - existing_alerts[0].created_at).total_seconds() > 3600:
                    create_alert(
                        db,
                        machine_id=prediction.machine_id,
                        severity=severity.value,
                        message=message,
                        failure_probability=prediction.failure_probability,
                        anomaly_score=prediction.anomaly_score
                    )
                    
                    # Record metrics
                    metrics_collector.record_alert(
                        severity=severity.value,
                        machine_id=prediction.machine_id
                    )
                    
                    alerts_created += 1
        
        structured_logger.info(
            "Auto-generated alerts",
            alerts_created=alerts_created,
            predictions_checked=len(recent_predictions)
        )
        
        return {
            "alerts_created": alerts_created,
            "predictions_checked": len(recent_predictions),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error auto-generating alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error auto-generating alerts"
        )


@router.get("/alerts/stats", tags=["alerts"])
async def get_alert_statistics(
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database)
):
    """
    Get alert statistics
    
    - **days**: Number of days to include in statistics
    """
    try:
        # Get alert statistics from database
        # This would typically query aggregated statistics
        # For now, return mock data
        
        stats = {
            "period_days": days,
            "total_alerts": 45,
            "unresolved_alerts": 12,
            "by_severity": {
                "CRITICAL": 2,
                "HIGH": 8,
                "MEDIUM": 15,
                "LOW": 20
            },
            "by_machine": {
                "M01": 12,
                "M02": 8,
                "M03": 15,
                "M04": 10
            },
            "resolution_time": {
                "average_hours": 4.5,
                "median_hours": 2.1,
                "max_hours": 24.0
            },
            "trends": {
                "alerts_today": 5,
                "alerts_yesterday": 3,
                "alerts_this_week": 18,
                "alerts_last_week": 12
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting alert statistics"
        )
