# error_handling/error_monitoring.py
"""
Error Reporting and Monitoring System for Window Quotation System
Milestone 1.2: Error Handling & Resilience

Features:
- Error aggregation and analysis
- Real-time error alerting
- Error trends and patterns detection
- Integration with monitoring services
- Error recovery suggestions
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from enum import Enum

from error_handling.error_manager import ErrorDetail, ErrorCategory, ErrorSeverity
from error_handling.logging_config import get_logger


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class ErrorPattern:
    """Error pattern identification"""
    error_code: str
    category: ErrorCategory
    count: int
    first_seen: datetime
    last_seen: datetime
    affected_endpoints: List[str]
    user_impact_count: int
    pattern_hash: str


@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    error_code: str
    max_occurrences: int
    time_window_minutes: int
    alert_level: AlertLevel
    cooldown_minutes: int = 60


class ErrorAggregator:
    """Aggregate and analyze error patterns"""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.error_details = {}
        self.error_timestamps = defaultdict(list)
        self.endpoint_errors = defaultdict(set)
        self.user_errors = defaultdict(set)
        self.logger = get_logger()
    
    def record_error(
        self,
        error_detail: ErrorDetail,
        endpoint: str = None,
        user_id: str = None,
        ip_address: str = None
    ):
        """Record an error occurrence"""
        
        error_key = f"{error_detail.code}:{error_detail.category}"
        
        # Update counters
        self.error_counts[error_key] += 1
        
        # Store error details
        if error_key not in self.error_details:
            self.error_details[error_key] = {
                "code": error_detail.code,
                "category": error_detail.category,
                "severity": error_detail.severity,
                "message_es": error_detail.message_es,
                "message_en": error_detail.message_en,
                "first_seen": error_detail.timestamp,
                "sample_technical_details": error_detail.technical_details
            }
        
        # Update timestamps
        self.error_timestamps[error_key].append(error_detail.timestamp)
        
        # Track affected endpoints
        if endpoint:
            self.endpoint_errors[error_key].add(endpoint)
        
        # Track affected users
        if user_id:
            self.user_errors[error_key].add(user_id)
        
        # Log the error recording
        self.logger.info(
            f"Error recorded: {error_key}",
            error_code=error_detail.code,
            endpoint=endpoint,
            user_id=user_id,
            ip_address=ip_address
        )
    
    def get_error_patterns(self, hours_back: int = 24) -> List[ErrorPattern]:
        """Get error patterns for analysis"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        patterns = []
        
        for error_key, count in self.error_counts.items():
            if count == 0:
                continue
            
            # Filter timestamps to time window
            recent_timestamps = [
                ts for ts in self.error_timestamps[error_key]
                if ts >= cutoff_time
            ]
            
            if not recent_timestamps:
                continue
            
            error_details = self.error_details[error_key]
            
            # Create pattern hash for deduplication
            pattern_data = f"{error_details['code']}:{error_details['category']}:{error_details['message_en']}"
            pattern_hash = hashlib.md5(pattern_data.encode()).hexdigest()[:8]
            
            pattern = ErrorPattern(
                error_code=error_details['code'],
                category=error_details['category'],
                count=len(recent_timestamps),
                first_seen=min(recent_timestamps),
                last_seen=max(recent_timestamps),
                affected_endpoints=list(self.endpoint_errors.get(error_key, [])),
                user_impact_count=len(self.user_errors.get(error_key, [])),
                pattern_hash=pattern_hash
            )
            
            patterns.append(pattern)
        
        # Sort by impact (count * user_impact_count)
        patterns.sort(key=lambda p: p.count * max(1, p.user_impact_count), reverse=True)
        
        return patterns
    
    def get_error_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get comprehensive error summary"""
        
        patterns = self.get_error_patterns(hours_back)
        
        total_errors = sum(p.count for p in patterns)
        affected_users = sum(p.user_impact_count for p in patterns)
        
        # Category breakdown
        category_counts = Counter(p.category for p in patterns)
        
        # Severity breakdown
        severity_counts = defaultdict(int)
        for error_key in self.error_counts:
            if self.error_counts[error_key] > 0:
                error_details = self.error_details[error_key]
                severity_counts[error_details['severity']] += self.error_counts[error_key]
        
        return {
            "total_errors": total_errors,
            "unique_error_types": len(patterns),
            "affected_users": affected_users,
            "category_breakdown": dict(category_counts),
            "severity_breakdown": dict(severity_counts),
            "top_errors": [asdict(p) for p in patterns[:10]],
            "summary_period_hours": hours_back,
            "generated_at": datetime.now().isoformat()
        }


class AlertManager:
    """Manage error alerts and notifications"""
    
    def __init__(self):
        self.alert_thresholds = self._get_default_thresholds()
        self.alert_history = defaultdict(list)
        self.cooldown_tracker = {}
        self.logger = get_logger()
    
    def _get_default_thresholds(self) -> List[AlertThreshold]:
        """Get default alert thresholds"""
        return [
            # Critical errors
            AlertThreshold("DB_ERROR", 5, 10, AlertLevel.CRITICAL, 30),
            AlertThreshold("SECURITY_ERROR", 1, 5, AlertLevel.EMERGENCY, 15),
            AlertThreshold("UNEXPECTED_ERROR", 3, 15, AlertLevel.CRITICAL, 60),
            
            # High priority errors
            AlertThreshold("AUTH_ERROR", 10, 30, AlertLevel.WARNING, 60),
            AlertThreshold("VALIDATION_ERROR", 20, 60, AlertLevel.INFO, 120),
            AlertThreshold("BUSINESS_ERROR", 15, 30, AlertLevel.WARNING, 90),
        ]
    
    def check_alert_conditions(self, error_aggregator: ErrorAggregator) -> List[Dict[str, Any]]:
        """Check if any alert conditions are met"""
        
        alerts = []
        current_time = datetime.now()
        
        for threshold in self.alert_thresholds:
            # Check if we're in cooldown period
            cooldown_key = f"{threshold.error_code}:{threshold.alert_level}"
            if cooldown_key in self.cooldown_tracker:
                cooldown_until = self.cooldown_tracker[cooldown_key]
                if current_time < cooldown_until:
                    continue
            
            # Get recent errors for this threshold
            time_window = timedelta(minutes=threshold.time_window_minutes)
            cutoff_time = current_time - time_window
            
            error_count = 0
            for error_key, timestamps in error_aggregator.error_timestamps.items():
                if error_key.startswith(threshold.error_code):
                    recent_errors = [ts for ts in timestamps if ts >= cutoff_time]
                    error_count += len(recent_errors)
            
            # Check if threshold is exceeded
            if error_count >= threshold.max_occurrences:
                alert = self._create_alert(threshold, error_count, error_aggregator)
                alerts.append(alert)
                
                # Set cooldown
                cooldown_until = current_time + timedelta(minutes=threshold.cooldown_minutes)
                self.cooldown_tracker[cooldown_key] = cooldown_until
                
                # Log alert
                self.logger.error(
                    f"ALERT TRIGGERED: {threshold.error_code} - {error_count} errors in {threshold.time_window_minutes} minutes",
                    alert_level=threshold.alert_level,
                    error_code=threshold.error_code,
                    error_count=error_count
                )
        
        return alerts
    
    def _create_alert(
        self,
        threshold: AlertThreshold,
        error_count: int,
        aggregator: ErrorAggregator
    ) -> Dict[str, Any]:
        """Create alert data structure"""
        
        return {
            "alert_id": f"alert_{threshold.error_code}_{int(datetime.now().timestamp())}",
            "level": threshold.alert_level,
            "error_code": threshold.error_code,
            "title": f"Error Threshold Exceeded: {threshold.error_code}",
            "message": f"{error_count} occurrences of {threshold.error_code} in the last {threshold.time_window_minutes} minutes",
            "error_count": error_count,
            "threshold": threshold.max_occurrences,
            "time_window_minutes": threshold.time_window_minutes,
            "timestamp": datetime.now().isoformat(),
            "recommended_actions": self._get_recommended_actions(threshold.error_code),
        }
    
    def _get_recommended_actions(self, error_code: str) -> List[str]:
        """Get recommended actions for error types"""
        
        actions_map = {
            "DB_ERROR": [
                "Check database connectivity",
                "Verify database server status",
                "Review connection pool settings",
                "Check for blocked queries"
            ],
            "SECURITY_ERROR": [
                "Review security logs immediately",
                "Check for suspicious IP addresses",
                "Verify authentication systems",
                "Consider temporary access restrictions"
            ],
            "AUTH_ERROR": [
                "Check authentication service status",
                "Review failed login patterns",
                "Verify token validation logic",
                "Check session management"
            ],
            "VALIDATION_ERROR": [
                "Review input validation logic",
                "Check for malformed requests",
                "Verify client-side validation",
                "Update validation error messages"
            ],
            "BUSINESS_ERROR": [
                "Review business logic rules",
                "Check data consistency",
                "Verify calculation formulas",
                "Review user workflow"
            ]
        }
        
        return actions_map.get(error_code, [
            "Review error logs for details",
            "Check system resources",
            "Verify service dependencies",
            "Consider scaling if needed"
        ])


class ErrorMonitor:
    """Main error monitoring service"""
    
    def __init__(self):
        self.aggregator = ErrorAggregator()
        self.alert_manager = AlertManager()
        self.logger = get_logger()
        self.monitoring_enabled = True
    
    def record_error(
        self,
        error_detail: ErrorDetail,
        endpoint: str = None,
        user_id: str = None,
        ip_address: str = None
    ):
        """Record an error and check for alerts"""
        
        if not self.monitoring_enabled:
            return
        
        # Record the error
        self.aggregator.record_error(error_detail, endpoint, user_id, ip_address)
        
        # Check for alert conditions
        alerts = self.alert_manager.check_alert_conditions(self.aggregator)
        
        # Process any alerts
        for alert in alerts:
            self._process_alert(alert)
    
    def _process_alert(self, alert: Dict[str, Any]):
        """Process an alert (send notifications, etc.)"""
        
        # Log the alert (in production, you might send to external services)
        self.logger.critical(
            f"CRITICAL ALERT: {alert['title']}",
            alert_id=alert['alert_id'],
            alert_level=alert['level'],
            error_code=alert['error_code'],
            error_count=alert['error_count']
        )
        
        # In production, you might integrate with:
        # - Slack notifications
        # - Email alerts  
        # - PagerDuty
        # - Custom webhook endpoints
        
        # For now, we'll log structured alert data
        self.logger.error(
            "ALERT_DATA",
            extra={"alert_data": alert}
        )
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        
        # Get error summary for different time periods
        last_hour = self.aggregator.get_error_summary(1)
        last_24_hours = self.aggregator.get_error_summary(24)
        last_week = self.aggregator.get_error_summary(24 * 7)
        
        # Get recent error patterns
        recent_patterns = self.aggregator.get_error_patterns(24)
        
        return {
            "monitoring_status": "active" if self.monitoring_enabled else "disabled",
            "last_updated": datetime.now().isoformat(),
            "summaries": {
                "last_hour": last_hour,
                "last_24_hours": last_24_hours,
                "last_week": last_week
            },
            "recent_patterns": [asdict(p) for p in recent_patterns[:20]],
            "alert_thresholds": [asdict(t) for t in self.alert_manager.alert_thresholds],
            "active_cooldowns": len(self.alert_manager.cooldown_tracker)
        }
    
    def get_error_trends(self, days_back: int = 7) -> Dict[str, Any]:
        """Get error trends over time"""
        
        # This is a simplified version - in production you might want to store
        # historical data in a time-series database
        
        patterns = self.aggregator.get_error_patterns(days_back * 24)
        
        # Group by day
        daily_counts = defaultdict(int)
        category_trends = defaultdict(lambda: defaultdict(int))
        
        for pattern in patterns:
            # Simplified daily grouping
            day_key = pattern.first_seen.strftime("%Y-%m-%d")
            daily_counts[day_key] += pattern.count
            category_trends[pattern.category][day_key] += pattern.count
        
        return {
            "period_days": days_back,
            "daily_error_counts": dict(daily_counts),
            "category_trends": {k: dict(v) for k, v in category_trends.items()},
            "total_errors": sum(daily_counts.values()),
            "trend_direction": self._calculate_trend_direction(daily_counts)
        }
    
    def _calculate_trend_direction(self, daily_counts: Dict[str, int]) -> str:
        """Calculate if errors are trending up, down, or stable"""
        
        if len(daily_counts) < 2:
            return "insufficient_data"
        
        sorted_days = sorted(daily_counts.keys())
        recent_days = sorted_days[-3:]  # Last 3 days
        earlier_days = sorted_days[:-3] if len(sorted_days) > 3 else sorted_days[:-1]
        
        if not earlier_days:
            return "insufficient_data"
        
        recent_avg = sum(daily_counts[day] for day in recent_days) / len(recent_days)
        earlier_avg = sum(daily_counts[day] for day in earlier_days) / len(earlier_days)
        
        if recent_avg > earlier_avg * 1.2:
            return "increasing"
        elif recent_avg < earlier_avg * 0.8:
            return "decreasing"
        else:
            return "stable"


# === GLOBAL INSTANCE ===
error_monitor = ErrorMonitor()


def record_error_for_monitoring(
    error_detail: ErrorDetail,
    endpoint: str = None,
    user_id: str = None,
    ip_address: str = None
):
    """Global function to record errors for monitoring"""
    error_monitor.record_error(error_detail, endpoint, user_id, ip_address)


def get_monitoring_data() -> Dict[str, Any]:
    """Get current monitoring data"""
    return error_monitor.get_monitoring_dashboard_data()