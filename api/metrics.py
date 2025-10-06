"""
Prometheus metrics for the predictive maintenance API
"""

from prometheus_client import Counter, Histogram, REGISTRY
import logging

logger = logging.getLogger(__name__)

# Global variables to store metrics
REQUEST_COUNT = None
REQUEST_DURATION = None

def get_metrics():
    """Get or create metrics, ensuring no duplicates"""
    global REQUEST_COUNT, REQUEST_DURATION
    
    # Always create new instances - let Prometheus handle duplicates
    try:
        REQUEST_COUNT = Counter(
            'pdm_requests_total', 
            'Total API requests', 
            ['method', 'endpoint', 'status']
        )
        REQUEST_DURATION = Histogram(
            'pdm_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        logger.info("Prometheus metrics initialized")
    except ValueError as e:
        logger.warning(f"Metrics already registered: {e}")
        # Even if registered, create instances for use
        REQUEST_COUNT = Counter(
            'pdm_requests_total', 
            'Total API requests', 
            ['method', 'endpoint', 'status']
        )
        REQUEST_DURATION = Histogram(
            'pdm_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
    
    return REQUEST_COUNT, REQUEST_DURATION
