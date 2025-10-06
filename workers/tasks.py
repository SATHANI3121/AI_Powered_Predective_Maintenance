"""
Background task definitions for the predictive maintenance system
"""

import logging
from typing import List, Dict, Any
from rq import Queue
from redis import Redis
import pandas as pd
from ai.features import build_features
from ai.model_infer import MLService
from persistence.db import get_db
from persistence.models import SensorReading, Alert

logger = logging.getLogger(__name__)

# Redis connection
redis_conn = Redis(host='localhost', port=6379, db=0)
queue = Queue('maintenance', connection=redis_conn)


def process_sensor_data_async(file_path: str, machine_id: str) -> Dict[str, Any]:
    """
    Process uploaded sensor data file asynchronously
    
    Args:
        file_path: Path to the uploaded CSV file
        machine_id: ID of the machine the data belongs to
        
    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Processing sensor data for machine {machine_id} from {file_path}")
        
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Build features
        features = build_features(df)
        
        if features.empty:
            logger.warning(f"No features generated for machine {machine_id}")
            return {"status": "warning", "message": "No features generated"}
        
        # Get predictions
        ml_service = MLService()
        failure_prediction = ml_service.predict_failure_probability(features)
        anomaly_score = ml_service.detect_anomaly(features)
        
        # Store results in database
        db = next(get_db())
        
        # Create sensor readings
        for _, row in df.iterrows():
            reading = SensorReading(
                machine_id=machine_id,
                sensor=row['sensor'],
                value=row['value'],
                timestamp=row['timestamp']
            )
            db.add(reading)
        
        # Create alerts if needed
        if failure_prediction > 0.7:
            alert = Alert(
                machine_id=machine_id,
                alert_type="failure_risk",
                severity="high",
                message=f"High failure risk detected: {failure_prediction:.2f}",
                timestamp=pd.Timestamp.now()
            )
            db.add(alert)
        
        if anomaly_score > 0.8:
            alert = Alert(
                machine_id=machine_id,
                alert_type="anomaly",
                severity="medium",
                message=f"Anomaly detected with score: {anomaly_score:.2f}",
                timestamp=pd.Timestamp.now()
            )
            db.add(alert)
        
        db.commit()
        
        logger.info(f"Successfully processed data for machine {machine_id}")
        return {
            "status": "success",
            "failure_prediction": failure_prediction,
            "anomaly_score": anomaly_score,
            "records_processed": len(df)
        }
        
    except Exception as e:
        logger.error(f"Error processing sensor data: {str(e)}")
        return {"status": "error", "message": str(e)}


def enqueue_sensor_processing(file_path: str, machine_id: str) -> str:
    """
    Enqueue sensor data processing task
    
    Args:
        file_path: Path to the uploaded CSV file
        machine_id: ID of the machine
        
    Returns:
        Job ID for tracking
    """
    job = queue.enqueue(
        process_sensor_data_async,
        file_path,
        machine_id,
        timeout='10m'
    )
    
    logger.info(f"Enqueued processing job {job.id} for machine {machine_id}")
    return job.id
