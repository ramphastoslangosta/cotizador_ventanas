# error_handling/database_resilience.py
"""
Database Resilience Module for Window Quotation System
Milestone 1.2: Error Handling & Resilience

Features:
- Database connection retry logic with exponential backoff
- Graceful degradation for database failures
- Connection pool monitoring and recovery
- Circuit breaker pattern for database operations
- Health check functionality
"""

import time
import random
from typing import Optional, Callable, Any, Dict, List
from contextlib import contextmanager
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError
from error_handling.error_manager import (
    DatabaseError, ErrorMessages, create_database_error, error_manager
)
from error_handling.logging_config import get_logger


class ConnectionState(str, Enum):
    """Database connection states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered


class DatabaseHealthCheck:
    """Database health monitoring"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = get_logger()
    
    def check_connection(self) -> bool:
        """Check if database connection is healthy"""
        try:
            # Simple query to test connection
            result = self.db_session.execute(text("SELECT 1"))
            return result.fetchone() is not None
        except Exception as e:
            self.logger.database_error("health_check", f"Connection check failed: {str(e)}")
            return False
    
    def check_query_performance(self) -> Dict[str, Any]:
        """Check database query performance"""
        try:
            start_time = time.time()
            self.db_session.execute(text("SELECT COUNT(*) FROM app_materials"))
            query_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "query_time_ms": query_time,
                "performance_status": "good" if query_time < 1000 else "slow"
            }
        except Exception as e:
            self.logger.database_error("performance_check", f"Performance check failed: {str(e)}")
            return {
                "query_time_ms": -1,
                "performance_status": "failed"
            }


class CircuitBreaker:
    """Circuit breaker for database operations"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = SQLAlchemyError
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self.logger = get_logger()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise DatabaseError(
                    message_es="El servicio de base de datos no está disponible temporalmente.",
                    message_en="Database service temporarily unavailable",
                    technical_details="Circuit breaker is OPEN"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise DatabaseError(
                message_es="Error al acceder a la base de datos. Inténtelo de nuevo.",
                message_en="Database access error",
                technical_details=str(e)
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset"""
        return (
            time.time() - self.last_failure_time > self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.logger.info("Circuit breaker reset to CLOSED")
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.error(f"Circuit breaker opened after {self.failure_count} failures")


class DatabaseRetryHandler:
    """Handle database operations with retry logic"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.logger = get_logger()
        
        # Circuit breaker for database operations
        self.circuit_breaker = CircuitBreaker()
    
    def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute database operation with retry logic
        
        Args:
            operation: Function to execute
            operation_name: Name of the operation for logging
            *args, **kwargs: Arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            DatabaseError: If all retries fail
        """
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.database_operation(
                    operation_name, 
                    f"Attempt {attempt + 1}/{self.max_retries + 1}"
                )
                
                # Use circuit breaker
                result = self.circuit_breaker.call(operation, *args, **kwargs)
                
                if attempt > 0:
                    self.logger.database_operation(
                        operation_name,
                        f"Succeeded on attempt {attempt + 1}"
                    )
                
                return result
                
            except DatabaseError as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    self.logger.database_error(
                        operation_name,
                        f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e.message_en}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.database_error(
                        operation_name,
                        f"All {self.max_retries + 1} attempts failed"
                    )
                    break
            
            except Exception as e:
                # Unexpected error, don't retry
                last_exception = DatabaseError(
                    message_es="Error inesperado en la base de datos.",
                    message_en=f"Unexpected database error: {str(e)}",
                    technical_details=str(e)
                )
                break
        
        # All retries failed
        if last_exception:
            raise last_exception
        else:
            raise create_database_error("DB_QUERY_FAILED")
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry with exponential backoff"""
        
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add jitter to prevent thundering herd
            delay *= (0.5 + random.random() * 0.5)
        
        return delay


class DatabaseConnectionManager:
    """Manage database connections with resilience features"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.connection_state = ConnectionState.HEALTHY
        self.last_health_check = None
        self.health_check_interval = 300  # 5 minutes
        self.logger = get_logger()
        self.retry_handler = DatabaseRetryHandler()
        
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections every hour
                pool_size=10,        # Connection pool size
                max_overflow=20,     # Max overflow connections
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "VentanasApp"
                }
            )
            
            self.session_factory = sessionmaker(bind=self.engine)
            self.connection_state = ConnectionState.HEALTHY
            self.logger.database_operation("initialize", "Database connection initialized")
            
        except Exception as e:
            self.connection_state = ConnectionState.FAILED
            self.logger.database_error("initialize", f"Failed to initialize database: {str(e)}")
            raise create_database_error("DB_CONNECTION_FAILED", str(e))
    
    @contextmanager
    def get_session(self):
        """Get database session with error handling"""
        session = None
        try:
            session = self.session_factory()
            
            # Check if we need to verify connection health
            if self._should_check_health():
                self._check_connection_health(session)
            
            yield session
            session.commit()
            
        except Exception as e:
            if session:
                session.rollback()
            
            # Update connection state
            if isinstance(e, (DisconnectionError, TimeoutError)):
                self.connection_state = ConnectionState.FAILED
            
            self.logger.database_error("session", f"Session error: {str(e)}")
            raise
            
        finally:
            if session:
                session.close()
    
    def _should_check_health(self) -> bool:
        """Check if health check is needed"""
        if self.last_health_check is None:
            return True
        
        return (
            datetime.now() - self.last_health_check
        ).total_seconds() > self.health_check_interval
    
    def _check_connection_health(self, session: Session):
        """Check and update connection health"""
        health_checker = DatabaseHealthCheck(session)
        
        try:
            if health_checker.check_connection():
                if self.connection_state != ConnectionState.HEALTHY:
                    self.logger.database_operation("health_check", "Connection recovered")
                    self.connection_state = ConnectionState.HEALTHY
            else:
                self.connection_state = ConnectionState.DEGRADED
                self.logger.database_error("health_check", "Connection degraded")
                
        except Exception as e:
            self.connection_state = ConnectionState.FAILED
            self.logger.database_error("health_check", f"Health check failed: {str(e)}")
        
        finally:
            self.last_health_check = datetime.now()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current database health status"""
        try:
            with self.get_session() as session:
                health_checker = DatabaseHealthCheck(session)
                connection_ok = health_checker.check_connection()
                performance = health_checker.check_query_performance()
                
                return {
                    "status": self.connection_state.value,
                    "connection_ok": connection_ok,
                    "last_check": self.last_health_check.isoformat() if self.last_health_check else None,
                    "performance": performance,
                    "circuit_breaker_state": self.retry_handler.circuit_breaker.state.value
                }
                
        except Exception as e:
            return {
                "status": "error",
                "connection_ok": False,
                "error": str(e),
                "circuit_breaker_state": self.retry_handler.circuit_breaker.state.value
            }


# === GRACEFUL DEGRADATION UTILITIES ===
class FallbackDataProvider:
    """Provide fallback data when database is unavailable"""
    
    def __init__(self):
        self.logger = get_logger()
    
    def get_basic_materials(self) -> List[Dict[str, Any]]:
        """Return basic materials list for fallback"""
        self.logger.info("Using fallback materials data")
        
        return [
            {
                "id": "fallback_1",
                "name": "Perfil Básico",
                "code": "FALLBACK-001",
                "unit": "ML",
                "cost_per_unit": 50.0,
                "category": "Perfiles"
            }
        ]
    
    def get_basic_products(self) -> List[Dict[str, Any]]:
        """Return basic products list for fallback"""
        self.logger.info("Using fallback products data")
        
        return [
            {
                "id": "fallback_product_1",
                "name": "Ventana Básica",
                "window_type": "CORREDIZA",
                "aluminum_line": "SERIE_3"
            }
        ]


# === GLOBAL INSTANCES ===
# These will be initialized in main.py
db_connection_manager: Optional[DatabaseConnectionManager] = None
fallback_provider = FallbackDataProvider()


def initialize_database_resilience(database_url: str) -> DatabaseConnectionManager:
    """Initialize database resilience system"""
    global db_connection_manager
    
    db_connection_manager = DatabaseConnectionManager(database_url)
    logger = get_logger()
    logger.info("Database resilience system initialized")
    
    return db_connection_manager


def get_resilient_db_session():
    """Get database session with resilience features"""
    global db_connection_manager
    
    if db_connection_manager is None:
        raise RuntimeError("Database resilience not initialized")
    
    return db_connection_manager.get_session()


def execute_with_fallback(
    database_operation: Callable,
    fallback_operation: Callable,
    operation_name: str
) -> Any:
    """Execute operation with database fallback"""
    logger = get_logger()
    
    try:
        return database_operation()
    except DatabaseError as e:
        logger.error(
            f"Database operation {operation_name} failed, using fallback: {e.message_en}"
        )
        return fallback_operation()
    except Exception as e:
        logger.error(
            f"Unexpected error in {operation_name}, using fallback: {str(e)}"
        )
        return fallback_operation()