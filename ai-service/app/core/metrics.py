"""Prometheus metrics for AI service workers."""

from prometheus_client import Counter, Gauge, Histogram

kb_build_tasks_total = Counter(
    "kb_build_tasks_total",
    "Total KB build tasks by status",
    ["status"],
)

kb_build_tasks_running = Gauge(
    "kb_build_tasks_running",
    "Currently running KB build tasks",
)

kb_build_task_duration_seconds = Histogram(
    "kb_build_task_duration_seconds",
    "KB build task duration in seconds",
    ["task_type"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)

kb_build_tasks_failed_total = Counter(
    "kb_build_tasks_failed_total",
    "Failed KB build tasks by error code",
    ["error_code"],
)
