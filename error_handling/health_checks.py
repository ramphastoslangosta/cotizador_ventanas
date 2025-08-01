# error_handling/health_checks.py
"""
Health Check Endpoints for Window Quotation System
Milestone 1.2: Error Handling & Resilience

Features:
- System health monitoring endpoints
- Database connectivity checks
- Service availability monitoring
- Performance metrics collection
- Detailed diagnostics for troubleshooting
"""

import time
import psutil
import platform
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from error_handling.logging_config import get_logger
from error_handling.database_resilience import db_connection_manager


class HealthStatus(BaseModel):
    """Health check response model"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    version: str
    uptime_seconds: float
    checks: Dict[str, Any]


class ServiceCheck(BaseModel):
    """Individual service check result"""
    name: str
    status: str
    message: str
    response_time_ms: float
    details: Dict[str, Any] = {}


class SystemMetrics(BaseModel):
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    uptime_seconds: float


class HealthCheckManager:
    """Manage all health checks"""
    
    def __init__(self):
        self.logger = get_logger()
        self.start_time = time.time()
        self.app_version = "5.0.0"
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time
    
    def check_database(self, db: Session) -> ServiceCheck:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            # Test basic connection
            db.execute("SELECT 1")
            
            # Test a more complex query
            result = db.execute("SELECT COUNT(*) as count FROM app_materials")
            materials_count = result.fetchone()[0]
            
            response_time = (time.time() - start_time) * 1000
            
            # Get database health from connection manager
            db_health = {}
            if db_connection_manager:
                db_health = db_connection_manager.get_health_status()
            
            return ServiceCheck(
                name="database",
                status="healthy",
                message="Database connection successful",
                response_time_ms=response_time,
                details={
                    "materials_count": materials_count,
                    "connection_pool_status": db_health.get("status", "unknown"),
                    "circuit_breaker_state": db_health.get("circuit_breaker_state", "unknown")
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.database_error("health_check", f"Database health check failed: {str(e)}")
            
            return ServiceCheck(
                name="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                response_time_ms=response_time,
                details={"error": str(e)}
            )
    
    def check_system_resources(self) -> ServiceCheck:
        """Check system resource usage"""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            status = "healthy"
            if cpu_percent > 80 or memory.percent > 85 or disk.percent > 90:
                status = "degraded"
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                status = "unhealthy"
            
            return ServiceCheck(
                name="system_resources",
                status=status,
                message=f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%",
                response_time_ms=response_time,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return ServiceCheck(
                name="system_resources",
                status="unhealthy",
                message=f"Failed to get system metrics: {str(e)}",
                response_time_ms=response_time,
                details={"error": str(e)}
            )
    
    def check_application_services(self) -> ServiceCheck:
        """Check application-specific services"""
        start_time = time.time()
        
        try:
            # Check if critical modules are loadable
            from services.product_bom_service_db import ProductBOMServiceDB
            from security.formula_evaluator import formula_evaluator
            from security.middleware import SecurityMiddleware
            
            # Test formula evaluator
            test_result = formula_evaluator.evaluate_formula("2 + 2", {})
            if test_result != 4:
                raise Exception("Formula evaluator test failed")
            
            response_time = (time.time() - start_time) * 1000
            
            return ServiceCheck(
                name="application_services",
                status="healthy",
                message="All application services operational",
                response_time_ms=response_time,
                details={
                    "formula_evaluator": "operational",
                    "security_middleware": "loaded",
                    "bom_service": "available"
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return ServiceCheck(
                name="application_services",
                status="unhealthy",
                message=f"Application services check failed: {str(e)}",
                response_time_ms=response_time,
                details={"error": str(e)}
            )
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "hostname": platform.node(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
    
    def get_comprehensive_health(self, db: Session) -> HealthStatus:
        """Get comprehensive health status"""
        checks = {}
        overall_status = "healthy"
        
        # Run all health checks
        db_check = self.check_database(db)
        checks["database"] = db_check.dict()
        
        resources_check = self.check_system_resources()
        checks["system_resources"] = resources_check.dict()
        
        services_check = self.check_application_services()
        checks["application_services"] = services_check.dict()
        
        # Determine overall status
        statuses = [db_check.status, resources_check.status, services_check.status]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        
        # Add system information
        checks["system_info"] = self.get_system_info()
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.now(),
            version=self.app_version,
            uptime_seconds=self.get_uptime(),
            checks=checks
        )


# === ROUTER SETUP ===
router = APIRouter(prefix="/health", tags=["Health Checks"])
health_manager = HealthCheckManager()


@router.get("/", response_model=Dict[str, str])
async def basic_health_check():
    """
    Basic health check endpoint
    Returns simple status for load balancers
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "ventanas-quotation-system"
    }


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - determines if service is ready to receive traffic
    Returns 200 if ready, 503 if not ready
    """
    try:
        # Check database connectivity
        db_check = health_manager.check_database(db)
        
        if db_check.status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready - database unavailable"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "database_status": db_check.status
        }
        
    except Exception as e:
        health_manager.logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/live")
async def liveness_check():
    """
    Liveness check - determines if service is alive
    Returns 200 if alive, 503 if dead
    """
    try:
        # Basic service liveness check
        uptime = health_manager.get_uptime()
        
        # Check if service has been running for reasonable time
        if uptime < 1:  # Less than 1 second might indicate restart loop
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service just started, not fully initialized"
            )
        
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime
        }
        
    except HTTPException:
        raise
    except Exception as e:
        health_manager.logger.error(f"Liveness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not alive: {str(e)}"
        )


@router.get("/detailed", response_model=HealthStatus)
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with comprehensive system information
    Use for monitoring and diagnostics
    """
    try:
        health_status = health_manager.get_comprehensive_health(db)
        
        # Log health check
        health_manager.logger.info(
            f"Health check completed - Status: {health_status.status}",
            health_status=health_status.status,
            uptime=health_status.uptime_seconds
        )
        
        return health_status
        
    except Exception as e:
        health_manager.logger.error(f"Detailed health check failed: {str(e)}")
        
        # Return unhealthy status with error information
        return HealthStatus(
            status="unhealthy",
            timestamp=datetime.now(),
            version=health_manager.app_version,
            uptime_seconds=health_manager.get_uptime(),
            checks={
                "error": {
                    "message": f"Health check failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
            }
        )


@router.get("/database")
async def database_health_check(db: Session = Depends(get_db)):
    """
    Specific database health check
    """
    try:
        db_check = health_manager.check_database(db)
        
        # Return appropriate HTTP status
        if db_check.status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=db_check.dict()
            )
        
        return db_check.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        health_manager.logger.database_error("health_check", f"Database health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/metrics", response_model=SystemMetrics)
async def system_metrics():
    """
    Get system performance metrics
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get network connections (approximate active connections)
        connections = len(psutil.net_connections())
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            active_connections=connections,
            uptime_seconds=health_manager.get_uptime()
        )
        
    except Exception as e:
        health_manager.logger.error(f"System metrics collection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect system metrics: {str(e)}"
        )


@router.get("/version")
async def version_info():
    """
    Get application version and build information
    """
    return {
        "version": health_manager.app_version,
        "build_date": "2025-07-28",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "uptime_seconds": health_manager.get_uptime(),
        "start_time": datetime.fromtimestamp(health_manager.start_time).isoformat()
    }