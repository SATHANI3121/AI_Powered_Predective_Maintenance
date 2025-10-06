"""
Telemetry and monitoring setup for the Predictive Maintenance API
"""

import logging
import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger(__name__)

# Prometheus metrics (moved to api/metrics.py to avoid conflicts)

PREDICTION_COUNT = Counter(
    'pdm_predictions_total',
    'Total number of predictions made',
    ['model_type', 'machine_id']
)

PREDICTION_DURATION = Histogram(
    'pdm_prediction_duration_seconds',
    'Prediction duration in seconds',
    ['model_type']
)

ANOMALY_COUNT = Counter(
    'pdm_anomalies_detected_total',
    'Total number of anomalies detected',
    ['machine_id', 'severity']
)

ALERT_COUNT = Counter(
    'pdm_alerts_created_total',
    'Total number of alerts created',
    ['severity', 'machine_id']
)

MODEL_ACCURACY = Gauge(
    'pdm_model_accuracy',
    'Model accuracy score',
    ['model_type', 'version']
)

MODEL_PRECISION = Gauge(
    'pdm_model_precision',
    'Model precision score',
    ['model_type', 'version']
)

MODEL_RECALL = Gauge(
    'pdm_model_recall',
    'Model recall score',
    ['model_type', 'version']
)

DATABASE_CONNECTIONS = Gauge(
    'pdm_database_connections_active',
    'Number of active database connections'
)

REDIS_CONNECTIONS = Gauge(
    'pdm_redis_connections_active',
    'Number of active Redis connections'
)

QUEUE_SIZE = Gauge(
    'pdm_queue_size',
    'Number of items in processing queue',
    ['queue_name']
)

# Custom metrics
FEATURE_ENGINEERING_DURATION = Histogram(
    'pdm_feature_engineering_duration_seconds',
    'Feature engineering duration in seconds'
)

RAG_QUERY_DURATION = Histogram(
    'pdm_rag_query_duration_seconds',
    'RAG query duration in seconds'
)

RAG_QUERY_COUNT = Counter(
    'pdm_rag_queries_total',
    'Total number of RAG queries',
    ['query_type']
)

FILE_UPLOAD_SIZE = Histogram(
    'pdm_file_upload_size_bytes',
    'File upload size in bytes',
    ['file_type']
)

FILE_PROCESSING_DURATION = Histogram(
    'pdm_file_processing_duration_seconds',
    'File processing duration in seconds',
    ['file_type']
)


class MetricsCollector:
    """Metrics collector for custom metrics"""
    
    def __init__(self):
        self.start_time = time.time()
    
    def record_prediction(self, model_type: str, machine_id: str, duration: float):
        """Record prediction metrics"""
        PREDICTION_COUNT.labels(model_type=model_type, machine_id=machine_id).inc()
        PREDICTION_DURATION.labels(model_type=model_type).observe(duration)
    
    def record_anomaly(self, machine_id: str, severity: str):
        """Record anomaly detection"""
        ANOMALY_COUNT.labels(machine_id=machine_id, severity=severity).inc()
    
    def record_alert(self, severity: str, machine_id: str):
        """Record alert creation"""
        ALERT_COUNT.labels(severity=severity, machine_id=machine_id).inc()
    
    def update_model_metrics(self, model_type: str, version: str, metrics: Dict[str, float]):
        """Update model performance metrics"""
        if 'accuracy' in metrics:
            MODEL_ACCURACY.labels(model_type=model_type, version=version).set(metrics['accuracy'])
        if 'precision' in metrics:
            MODEL_PRECISION.labels(model_type=model_type, version=version).set(metrics['precision'])
        if 'recall' in metrics:
            MODEL_RECALL.labels(model_type=model_type, version=version).set(metrics['recall'])
    
    def record_feature_engineering(self, duration: float):
        """Record feature engineering duration"""
        FEATURE_ENGINEERING_DURATION.observe(duration)
    
    def record_rag_query(self, query_type: str, duration: float):
        """Record RAG query metrics"""
        RAG_QUERY_COUNT.labels(query_type=query_type).inc()
        RAG_QUERY_DURATION.observe(duration)
    
    def record_file_upload(self, file_type: str, size_bytes: int, duration: float):
        """Record file upload metrics"""
        FILE_UPLOAD_SIZE.labels(file_type=file_type).observe(size_bytes)
        FILE_PROCESSING_DURATION.labels(file_type=file_type).observe(duration)
    
    def update_connection_metrics(self, db_connections: int, redis_connections: int):
        """Update connection metrics"""
        DATABASE_CONNECTIONS.set(db_connections)
        REDIS_CONNECTIONS.set(redis_connections)
    
    def update_queue_size(self, queue_name: str, size: int):
        """Update queue size metrics"""
        QUEUE_SIZE.labels(queue_name=queue_name).set(size)


def setup_telemetry():
    """Setup OpenTelemetry tracing"""
    try:
        # Create resource
        resource = Resource.create({
            "service.name": "pdm-api",
            "service.version": "1.0.0",
            "deployment.environment": "production"
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Setup OTLP exporter
        otlp_endpoint = "https://pdm-monitor.eastus.monitor.azure.com"
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        
        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        logger.info("OpenTelemetry tracing configured")
        
    except Exception as e:
        logger.warning(f"Failed to setup OpenTelemetry: {e}")


def setup_instrumentation(app):
    """Setup OpenTelemetry instrumentation"""
    try:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        
        # Instrument Redis
        RedisInstrumentor().instrument()
        
        # Instrument requests
        RequestsInstrumentor().instrument()
        
        logger.info("OpenTelemetry instrumentation configured")
        
    except Exception as e:
        logger.warning(f"Failed to setup instrumentation: {e}")


def start_prometheus_server(port: int = 9000):
    """Start Prometheus metrics server"""
    try:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start Prometheus server: {e}")


class StructuredLogger:
    """Structured logging for JSON output"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create JSON formatter
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data"""
        self.logger.critical(message, extra=kwargs)


def create_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Create a new span for tracing"""
    tracer = trace.get_tracer(__name__)
    span = tracer.start_span(name)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    return span


def log_request(method: str, endpoint: str, status_code: int, duration: float, **kwargs):
    """Log request with structured data"""
    logger.info(
        f"Request completed: {method} {endpoint}",
        extra={
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_seconds": duration,
            **kwargs
        }
    )


def log_prediction(model_type: str, machine_id: str, duration: float, **kwargs):
    """Log prediction with structured data"""
    logger.info(
        f"Prediction completed: {model_type} for {machine_id}",
        extra={
            "model_type": model_type,
            "machine_id": machine_id,
            "duration_seconds": duration,
            **kwargs
        }
    )


def log_anomaly(machine_id: str, severity: str, score: float, **kwargs):
    """Log anomaly detection with structured data"""
    logger.warning(
        f"Anomaly detected: {severity} for {machine_id}",
        extra={
            "machine_id": machine_id,
            "severity": severity,
            "anomaly_score": score,
            **kwargs
        }
    )


def log_alert(severity: str, machine_id: str, message: str, **kwargs):
    """Log alert creation with structured data"""
    logger.warning(
        f"Alert created: {severity} for {machine_id}",
        extra={
            "severity": severity,
            "machine_id": machine_id,
            "message": message,
            **kwargs
        }
    )


# Initialize structured logger
structured_logger = StructuredLogger("pdm-api")

