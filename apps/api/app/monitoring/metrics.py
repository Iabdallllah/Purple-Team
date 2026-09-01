from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import Response
from typing import Optional
import time
import psutil
import asyncio

# Custom registry
registry = CollectorRegistry()

# Episode metrics
episodes_total = Counter(
    'purple_episodes_total',
    'Total number of episodes',
    ['status', 'scenario'],
    registry=registry
)

episodes_duration = Histogram(
    'purple_episodes_duration_seconds',
    'Episode duration in seconds',
    ['scenario'],
    buckets=[30, 60, 120, 300, 600, 1200, 1800],
    registry=registry
)

episodes_active = Gauge(
    'purple_episodes_active',
    'Number of currently running episodes',
    registry=registry
)

# Attack metrics
attacks_total = Counter(
    'purple_attacks_total',
    'Total number of attacks executed',
    ['technique_id', 'attack_type', 'success'],
    registry=registry
)

attacks_duration = Histogram(
    'purple_attack_duration_seconds',
    'Attack execution duration in seconds',
    ['attack_type'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
    registry=registry
)

# Detection metrics
detections_total = Counter(
    'purple_detections_total',
    'Total number of detections',
    ['detection_type', 'detected'],
    registry=registry
)

detection_confidence = Histogram(
    'purple_detection_confidence',
    'Detection confidence score',
    ['detection_type'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=registry
)

# Response metrics
responses_total = Counter(
    'purple_responses_total',
    'Total number of responses applied',
    ['action_type', 'success'],
    registry=registry
)

response_duration = Histogram(
    'purple_response_duration_seconds',
    'Response application duration in seconds',
    ['action_type'],
    buckets=[0.1, 0.5, 1, 2, 5, 10],
    registry=registry
)

# Posture score metrics
posture_score = Gauge(
    'purple_posture_score',
    'Current security posture score',
    ['project_id'],
    registry=registry
)

detection_rate = Gauge(
    'purple_detection_rate',
    'Detection rate (0-1)',
    ['project_id'],
    registry=registry
)

mttr_seconds = Gauge(
    'purple_mttr_seconds',
    'Mean time to respond in seconds',
    ['project_id'],
    registry=registry
)

coverage_score = Gauge(
    'purple_coverage_score',
    'MITRE/OWASP coverage score (0-1)',
    ['project_id', 'category'],
    registry=registry
)

# System metrics
system_cpu_usage = Gauge(
    'purple_system_cpu_percent',
    'System CPU usage percentage',
    registry=registry
)

system_memory_usage = Gauge(
    'purple_system_memory_percent',
    'System memory usage percentage',
    registry=registry
)

system_disk_usage = Gauge(
    'purple_system_disk_percent',
    'System disk usage percentage',
    registry=registry
)

# API metrics
api_requests_total = Counter(
    'purple_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

api_request_duration = Histogram(
    'purple_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5],
    registry=registry
)

# Database metrics
db_connections_active = Gauge(
    'purple_db_connections_active',
    'Active database connections',
    registry=registry
)

db_query_duration = Histogram(
    'purple_db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1],
    registry=registry
)

# Redis metrics
redis_connections_active = Gauge(
    'purple_redis_connections_active',
    'Active Redis connections',
    registry=registry
)

redis_operations_total = Counter(
    'purple_redis_operations_total',
    'Total Redis operations',
    ['operation', 'status'],
    registry=registry
)

# Sandbox metrics
sandbox_containers_active = Gauge(
    'purple_sandbox_containers_active',
    'Active sandbox containers',
    registry=registry
)

sandbox_container_duration = Histogram(
    'purple_sandbox_container_duration_seconds',
    'Sandbox container lifetime in seconds',
    buckets=[60, 300, 600, 1200, 1800, 3600],
    registry=registry
)

# RAG metrics
rag_queries_total = Counter(
    'purple_rag_queries_total',
    'Total RAG queries',
    ['type', 'status'],
    registry=registry
)

rag_query_duration = Histogram(
    'purple_rag_query_duration_seconds',
    'RAG query duration in seconds',
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5],
    registry=registry
)

# LLM metrics
llm_requests_total = Counter(
    'purple_llm_requests_total',
    'Total LLM requests',
    ['model', 'status'],
    registry=registry
)

llm_tokens_total = Counter(
    'purple_llm_tokens_total',
    'Total LLM tokens used',
    ['model', 'type'],
    registry=registry
)

llm_request_duration = Histogram(
    'purple_llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['model'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60],
    registry=registry
)


# FastAPI instrumentator setup
def setup_instrumentator(app):
    """Setup Prometheus FastAPI instrumentator"""
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/metrics", "/socket.io"],
        inprogress_name="purple_api_requests_inprogress",
        inprogress_labels=True,
    )
    
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    return instrumentator


# Custom metrics endpoint
async def metrics_endpoint():
    """Custom metrics endpoint with all metrics"""
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )


# Background task to update system metrics
async def update_system_metrics():
    """Periodically update system metrics"""
    while True:
        try:
            # CPU
            system_cpu_usage.set(psutil.cpu_percent(interval=1))
            
            # Memory
            mem = psutil.virtual_memory()
            system_memory_usage.set(mem.percent)
            
            # Disk
            disk = psutil.disk_usage('/')
            system_disk_usage.set((disk.used / disk.total) * 100)
            
        except Exception as e:
            print(f"Error updating system metrics: {e}")
        
        await asyncio.sleep(30)


# Decorator for timing async functions
def observe_duration(metric: Histogram, labels: dict = None):
    """Decorator to observe function duration"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels, status="error").observe(duration)
                else:
                    metric.labels(status="error").observe(duration)
                raise
        return wrapper
    return decorator


# Helper functions for recording metrics
def record_episode_start(scenario: str):
    episodes_total.labels(status="started", scenario=scenario).inc()
    episodes_active.inc()


def record_episode_end(scenario: str, status: str, duration: float):
    episodes_total.labels(status=status, scenario=scenario).inc()
    episodes_duration.labels(scenario=scenario).observe(duration)
    episodes_active.dec()


def record_attack(technique_id: str, attack_type: str, success: bool, duration: float):
    attacks_total.labels(
        technique_id=technique_id,
        attack_type=attack_type,
        success=str(success).lower()
    ).inc()
    attacks_duration.labels(attack_type=attack_type).observe(duration)


def record_detection(detection_type: str, detected: bool, confidence: float):
    detections_total.labels(
        detection_type=detection_type,
        detected=str(detected).lower()
    ).inc()
    if confidence > 0:
        detection_confidence.labels(detection_type=detection_type).observe(confidence)


def record_response(action_type: str, success: bool, duration: float):
    responses_total.labels(
        action_type=action_type,
        success=str(success).lower()
    ).inc()
    response_duration.labels(action_type=action_type).observe(duration)


def update_posture_metrics(project_id: str, score: float, detection_rate_val: float, mttr: float, coverage: dict):
    posture_score.labels(project_id=project_id).set(score)
    detection_rate.labels(project_id=project_id).set(detection_rate_val)
    mttr_seconds.labels(project_id=project_id).set(mttr)
    for category, cov in coverage.items():
        if isinstance(cov, dict) and 'coverage' in cov:
            coverage_score.labels(project_id=project_id, category=category).set(cov['coverage'])


def record_api_request(method: str, endpoint: str, status: int, duration: float):
    api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=str(status)
    ).inc()
    api_request_duration.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def record_db_query(query_type: str, duration: float):
    db_query_duration.labels(query_type=query_type).observe(duration)


def record_redis_operation(operation: str, success: bool):
    redis_operations_total.labels(
        operation=operation,
        status="success" if success else "error"
    ).inc()


def record_sandbox_container_start():
    sandbox_containers_active.inc()


def record_sandbox_container_end(duration: float):
    sandbox_containers_active.dec()
    sandbox_container_duration.observe(duration)


def record_rag_query(query_type: str, success: bool, duration: float):
    rag_queries_total.labels(
        type=query_type,
        status="success" if success else "error"
    ).inc()
    rag_query_duration.observe(duration)


def record_llm_request(model: str, success: bool, duration: float, input_tokens: int = 0, output_tokens: int = 0):
    llm_requests_total.labels(
        model=model,
        status="success" if success else "error"
    ).inc()
    llm_request_duration.labels(model=model).observe(duration)
    if input_tokens > 0:
        llm_tokens_total.labels(model=model, type="input").inc(input_tokens)
    if output_tokens > 0:
        llm_tokens_total.labels(model=model, type="output").inc(output_tokens)