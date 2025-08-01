# error_handling/logging_config.py
"""
Comprehensive Logging System for Window Quotation System
Milestone 1.2: Error Handling & Resilience

Features:
- Structured logging with JSON format
- Multiple log levels and handlers
- Separate log files for different components
- Log rotation and retention
- Security event logging
- Performance monitoring integration
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'ip_address'):
            log_entry["ip_address"] = record.ip_address
        if hasattr(record, 'endpoint'):
            log_entry["endpoint"] = record.endpoint
        if hasattr(record, 'method'):
            log_entry["method"] = record.method
        if hasattr(record, 'response_time'):
            log_entry["response_time_ms"] = record.response_time
        
        return json.dumps(log_entry, ensure_ascii=False)


class LoggingConfig:
    """Centralized logging configuration"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Ensure log files exist
        self._ensure_log_files()
        
        # Setup loggers
        self._setup_loggers()
    
    def _ensure_log_files(self):
        """Ensure all log files exist"""
        log_files = [
            "application.log",
            "error.log", 
            "security.log",
            "database.log",
            "performance.log",
            "audit.log"
        ]
        
        for log_file in log_files:
            log_path = self.log_dir / log_file
            log_path.touch(exist_ok=True)
    
    def _setup_loggers(self):
        """Setup all application loggers"""
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remove default handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Application logger
        self._setup_application_logger()
        
        # Error logger
        self._setup_error_logger()
        
        # Security logger
        self._setup_security_logger()
        
        # Database logger
        self._setup_database_logger()
        
        # Performance logger
        self._setup_performance_logger()
        
        # Audit logger
        self._setup_audit_logger()
    
    def _setup_application_logger(self):
        """Setup main application logger"""
        logger = logging.getLogger("application")
        logger.setLevel(logging.INFO)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "application.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        logger.propagate = False
    
    def _setup_error_logger(self):
        """Setup error logger for all errors"""
        logger = logging.getLogger("error_manager")
        logger.setLevel(logging.WARNING)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10  # Keep more error logs
        )
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.WARNING)
        logger.addHandler(handler)
        
        logger.propagate = False
    
    def _setup_security_logger(self):
        """Setup security event logger"""
        logger = logging.getLogger("security")
        logger.setLevel(logging.WARNING)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "security.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=20  # Keep many security logs
        )
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.WARNING)
        logger.addHandler(handler)
        
        logger.propagate = False
    
    def _setup_database_logger(self):
        """Setup database operation logger"""
        logger = logging.getLogger("database")
        logger.setLevel(logging.INFO)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "database.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=7
        )
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        logger.propagate = False
    
    def _setup_performance_logger(self):
        """Setup performance monitoring logger"""
        logger = logging.getLogger("performance")
        logger.setLevel(logging.INFO)
        
        # File handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "performance.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        logger.propagate = False
    
    def _setup_audit_logger(self):
        """Setup audit trail logger"""
        logger = logging.getLogger("audit")
        logger.setLevel(logging.INFO)
        
        # File handler with rotation (no size limit for audit logs)
        handler = logging.handlers.TimedRotatingFileHandler(
            self.log_dir / "audit.log",
            when='midnight',
            interval=1,
            backupCount=30  # Keep 30 days of audit logs
        )
        handler.setFormatter(JSONFormatter())
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        logger.propagate = False


class ApplicationLogger:
    """High-level logging interface for the application"""
    
    def __init__(self):
        self.app_logger = logging.getLogger("application")
        self.error_logger = logging.getLogger("error_manager")
        self.security_logger = logging.getLogger("security")
        self.db_logger = logging.getLogger("database")
        self.performance_logger = logging.getLogger("performance")
        self.audit_logger = logging.getLogger("audit")
    
    def info(self, message: str, **extra):
        """Log informational message"""
        self.app_logger.info(message, extra=extra)
    
    def warning(self, message: str, **extra):
        """Log warning message"""
        self.app_logger.warning(message, extra=extra)
    
    def error(self, message: str, **extra):
        """Log error message"""
        self.error_logger.error(message, extra=extra)
    
    def critical(self, message: str, **extra):
        """Log critical error message"""
        self.error_logger.critical(message, extra=extra)
    
    def security_event(self, event_type: str, message: str, **extra):
        """Log security event"""
        extra["event_type"] = event_type
        self.security_logger.warning(f"SECURITY EVENT: {event_type} - {message}", extra=extra)
    
    def database_operation(self, operation: str, message: str, **extra):
        """Log database operation"""
        extra["operation"] = operation
        self.db_logger.info(f"DB {operation}: {message}", extra=extra)
    
    def database_error(self, operation: str, error: str, **extra):
        """Log database error"""
        extra["operation"] = operation
        self.db_logger.error(f"DB ERROR {operation}: {error}", extra=extra)
    
    def performance_metric(self, metric_name: str, value: float, unit: str = "ms", **extra):
        """Log performance metric"""
        extra.update({
            "metric_name": metric_name,
            "value": value,
            "unit": unit
        })
        self.performance_logger.info(f"PERFORMANCE {metric_name}: {value}{unit}", extra=extra)
    
    def audit_event(self, action: str, resource: str, user_id: str = None, result: str = "success", **extra):
        """Log audit event"""
        extra.update({
            "action": action,
            "resource": resource,
            "user_id": user_id,
            "result": result
        })
        self.audit_logger.info(f"AUDIT {action} on {resource}: {result}", extra=extra)


# === REQUEST LOGGING UTILITIES ===
def log_request_start(logger: ApplicationLogger, method: str, endpoint: str, user_id: str = None, **extra):
    """Log the start of a request"""
    logger.info(
        f"Request started: {method} {endpoint}",
        method=method,
        endpoint=endpoint,
        user_id=user_id,
        **extra
    )


def log_request_end(logger: ApplicationLogger, method: str, endpoint: str, status_code: int, 
                   response_time: float, user_id: str = None, **extra):
    """Log the end of a request"""
    logger.info(
        f"Request completed: {method} {endpoint} - {status_code} ({response_time:.2f}ms)",
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        response_time=response_time,
        user_id=user_id,
        **extra
    )
    
    # Also log performance metric
    logger.performance_metric(
        "request_duration",
        response_time,
        "ms",
        endpoint=endpoint,
        method=method,
        status_code=status_code
    )


# === INITIALIZE LOGGING ===
def initialize_logging(log_dir: str = "logs") -> ApplicationLogger:
    """Initialize the logging system and return application logger"""
    
    # Setup logging configuration
    logging_config = LoggingConfig(log_dir)
    
    # Create application logger
    app_logger = ApplicationLogger()
    
    # Log initialization
    app_logger.info("Logging system initialized successfully", log_dir=log_dir)
    
    return app_logger


# === GLOBAL LOGGER INSTANCE ===
# This will be initialized in main.py
app_logger: Optional[ApplicationLogger] = None


def get_logger() -> ApplicationLogger:
    """Get the global application logger instance"""
    global app_logger
    if app_logger is None:
        app_logger = initialize_logging()
    return app_logger