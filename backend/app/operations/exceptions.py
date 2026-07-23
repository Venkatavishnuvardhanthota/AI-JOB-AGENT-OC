from __future__ import annotations


class OperationsError(Exception):
    pass


class LoggingError(OperationsError):
    pass


class TracingError(OperationsError):
    pass


class MetricsError(OperationsError):
    pass


class HealthCheckError(OperationsError):
    pass


class DiagnosticsError(OperationsError):
    pass


class HistoryError(OperationsError):
    pass


class ReportError(OperationsError):
    pass


class ExportError(OperationsError):
    pass
