"""
Data ingestion endpoints for sensor data upload
"""

import logging
import time
import pandas as pd
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.schemas import UploadResult, SensorReading, FileUploadResponse
from api.deps import get_database, verify_api_key, validate_file_upload, get_settings
from api.telemetry import structured_logger
# Metrics temporarily disabled: FILE_UPLOAD_SIZE, FILE_PROCESSING_DURATION
from persistence.db import insert_sensor_data, get_machine_by_id
from workers.tasks import process_sensor_data_async

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=UploadResult, tags=["ingestion"])
async def ingest_sensor_data(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database),
    settings = Depends(get_settings)
):
    """
    Upload and process sensor data CSV file
    
    - **file**: CSV file containing sensor readings
    - **format**: timestamp,machine_id,sensor,value
    - **max_size**: 100MB
    - **supported_types**: csv, txt
    """
    start_time = time.time()
    
    try:
        # Validate file
        file_size = 0
        content_type = file.content_type or "application/octet-stream"
        
        # Read file content to get size
        content = await file.read()
        file_size = len(content)
        
        # Validate file upload
        validate_file_upload(file_size, content_type, settings)
        
        # Reset file pointer
        await file.seek(0)
        
        # Parse CSV data
        try:
            df = pd.read_csv(file.file, parse_dates=['timestamp'])
            
            # Validate required columns
            required_columns = ['timestamp', 'machine_id', 'sensor', 'value']
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required columns: {missing_columns}"
                )
            
            # Validate data types and ranges
            validation_errors = []
            
            # Check timestamp format
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                validation_errors.append("timestamp column must be datetime format")
            
            # Check machine_id format
            if not df['machine_id'].str.match(r'^[A-Za-z0-9_-]+$').all():
                validation_errors.append("machine_id must contain only alphanumeric characters, hyphens, and underscores")
            
            # Check sensor values
            valid_sensors = ['vibration', 'temperature', 'pressure', 'rpm', 'current', 'voltage', 'speed']
            invalid_sensors = df[~df['sensor'].isin(valid_sensors)]['sensor'].unique()
            if len(invalid_sensors) > 0:
                validation_errors.append(f"Invalid sensor types: {list(invalid_sensors)}")
            
            # Check value ranges
            if df['value'].isna().any():
                validation_errors.append("value column cannot contain null values")
            
            if (df['value'] < -1000).any() or (df['value'] > 10000).any():
                validation_errors.append("value must be between -1000 and 10000")
            
            if validation_errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Data validation errors: {'; '.join(validation_errors)}"
                )
            
            # Check if machines exist
            unique_machines = df['machine_id'].unique()
            for machine_id in unique_machines:
                machine = get_machine_by_id(db, machine_id)
                if not machine:
                    logger.warning(f"Unknown machine_id: {machine_id}")
                    # Create machine if it doesn't exist (for demo purposes)
                    from persistence.models import Machine
                    new_machine = Machine(
                        machine_id=machine_id,
                        line="unknown",
                        criticality=3
                    )
                    db.add(new_machine)
                    db.commit()
            
            # Insert data into database
            rows_inserted = insert_sensor_data(db, df)
            
            # Queue background processing
            try:
                process_sensor_data_async.delay(df.to_dict('records'))
                logger.info(f"Queued {len(df)} records for background processing")
            except Exception as e:
                logger.warning(f"Failed to queue background processing: {e}")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Record metrics (temporarily disabled)
            # TODO: Re-enable metrics once server is stable
            
            # Log structured data
            structured_logger.info(
                "Sensor data ingested successfully",
                file_name=file.filename,
                file_size_bytes=file_size,
                rows_ingested=rows_inserted,
                processing_time_seconds=processing_time,
                machines=unique_machines.tolist()
            )
            
            return UploadResult(
                rows_ingested=rows_inserted,
                file_size_bytes=file_size,
                processing_time_seconds=processing_time
            )
            
        except pd.errors.EmptyDataError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty CSV file"
            )
        except pd.errors.ParserError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV parsing error: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during data ingestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during data ingestion"
        )


@router.post("/ingest/batch", response_model=UploadResult, tags=["ingestion"])
async def ingest_batch_sensor_data(
    readings: List[SensorReading],
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_database)
):
    """
    Upload sensor data as JSON batch
    
    - **readings**: List of sensor readings
    - **max_batch_size**: 1000 records
    """
    if len(readings) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size exceeds maximum of 1000 records"
        )
    
    try:
        # Convert to DataFrame
        data = []
        for reading in readings:
            data.append({
                'timestamp': reading.timestamp,
                'machine_id': reading.machine_id,
                'sensor': reading.sensor.value,
                'value': reading.value
            })
        
        df = pd.DataFrame(data)
        
        # Insert data
        rows_inserted = insert_sensor_data(db, df)
        
        # Queue background processing
        try:
            process_sensor_data_async.delay(data)
        except Exception as e:
            logger.warning(f"Failed to queue background processing: {e}")
        
        structured_logger.info(
            "Batch sensor data ingested successfully",
            rows_ingested=rows_inserted,
            batch_size=len(readings)
        )
        
        return UploadResult(
            rows_ingested=rows_inserted,
            file_size_bytes=0,  # No file for batch upload
            processing_time_seconds=0
        )
        
    except Exception as e:
        logger.error(f"Error during batch ingestion: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during batch ingestion"
        )


@router.get("/ingest/status/{job_id}", tags=["ingestion"])
async def get_ingestion_status(
    job_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get status of background ingestion job
    
    - **job_id**: Background job identifier
    """
    try:
        from workers.tasks import get_job_status
        
        status = get_job_status(job_id)
        return {
            "job_id": job_id,
            "status": status.get("status", "unknown"),
            "progress": status.get("progress", 0),
            "result": status.get("result"),
            "error": status.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job status"
        )


@router.get("/ingest/schema", tags=["ingestion"])
async def get_ingestion_schema():
    """
    Get CSV schema for data ingestion
    
    Returns the expected format and validation rules
    """
    return {
        "format": "CSV",
        "required_columns": [
            "timestamp",
            "machine_id", 
            "sensor",
            "value"
        ],
        "column_descriptions": {
            "timestamp": "ISO 8601 datetime format (e.g., 2024-01-01T12:00:00Z)",
            "machine_id": "Alphanumeric machine identifier (max 50 chars)",
            "sensor": "Sensor type: vibration, temperature, pressure, rpm, current, voltage",
            "value": "Numeric sensor reading (-1000 to 10000)"
        },
        "validation_rules": {
            "timestamp": "Must be valid datetime",
            "machine_id": "Alphanumeric with hyphens/underscores only",
            "sensor": "Must be one of: vibration, temperature, pressure, rpm, current, voltage",
            "value": "Numeric, no nulls, range -1000 to 10000"
        },
        "example": {
            "timestamp": "2024-01-01T12:00:00Z",
            "machine_id": "M01",
            "sensor": "vibration",
            "value": 0.42
        }
    }
