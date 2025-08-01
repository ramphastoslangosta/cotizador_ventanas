# data_protection/audit_trail.py
"""
Comprehensive Audit Trail System for Window Quotation System
Milestone 1.3: Data Protection

Features:
- Complete audit trail for all critical operations
- Immutable audit log storage
- Change tracking with before/after values
- User action tracking with context
- Compliance reporting capabilities
- Real-time audit event streaming
- Integration with existing logging system
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import threading
from collections import defaultdict

from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, create_engine, MetaData, Table
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID, JSONB

from error_handling.logging_config import get_logger
from error_handling.error_manager import create_database_error


class AuditAction(str, Enum):
    """Types of auditable actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SOFT_DELETE = "soft_delete"
    RESTORE = "restore"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE_BACKUP = "restore_backup"
    CONFIGURATION_CHANGE = "configuration_change"
    PERMISSION_CHANGE = "permission_change"
    SYSTEM_EVENT = "system_event"


class AuditLevel(str, Enum):
    """Audit importance levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    action: AuditAction
    resource_type: str
    resource_id: Optional[str]
    level: AuditLevel
    success: bool
    
    # Context information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # Change details
    changes: Optional[Dict[str, Any]] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    
    # Additional metadata
    description: str = ""
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Integrity
    checksum: Optional[str] = None


class AuditTrailManager:
    """
    Comprehensive audit trail management
    """
    
    def __init__(self, database_url: str, retention_days: int = 2555):  # 7 years default
        """
        Initialize audit trail manager
        
        Args:
            database_url: Database connection URL
            retention_days: Days to retain audit logs (default 7 years for compliance)
        """
        self.database_url = database_url
        self.retention_days = retention_days
        self.logger = get_logger()
        
        # Create audit log table
        self._create_audit_table()
        
        # Event buffers for batch processing
        self._event_buffer = []
        self._buffer_lock = threading.Lock()
        self._batch_size = 100
        
        # Statistics tracking
        self._stats = defaultdict(int)
    
    def _create_audit_table(self):
        """Create audit log table if it doesn't exist"""
        
        try:
            engine = create_engine(self.database_url)
            metadata = MetaData()
            
            # Define audit log table
            self.audit_table = Table(
                'audit_logs',
                metadata,
                Column('event_id', String(36), primary_key=True),
                Column('timestamp', DateTime, nullable=False, index=True),
                Column('user_id', String(36), index=True),
                Column('session_id', String(36), index=True),
                Column('action', String(50), nullable=False, index=True),
                Column('resource_type', String(100), nullable=False, index=True),
                Column('resource_id', String(36), index=True),
                Column('level', String(20), nullable=False, index=True),
                Column('success', Boolean, nullable=False),
                
                # Context
                Column('ip_address', String(45)),  # IPv6 compatible
                Column('user_agent', Text),
                Column('request_id', String(36)),
                
                # Changes
                Column('changes', JSONB),
                Column('old_values', JSONB),
                Column('new_values', JSONB),
                
                # Metadata
                Column('description', Text),
                Column('error_message', Text),
                Column('metadata', JSONB),
                
                # Integrity
                Column('checksum', String(64), nullable=False)
            )
            
            # Create table
            metadata.create_all(engine)
            
            self.logger.info("Audit trail table initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to create audit table: {str(e)}")
            raise create_database_error("DB_INITIALIZATION_FAILED", str(e))
    
    def log_event(
        self,
        action: AuditAction,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        level: AuditLevel = AuditLevel.MEDIUM,
        success: bool = True,
        description: str = "",
        changes: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        
        # Context
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> str:
        """
        Log an audit event
        
        Args:
            action: Type of action performed
            resource_type: Type of resource affected
            user_id: ID of user performing action
            resource_id: ID of specific resource
            level: Importance level of the event
            success: Whether the action was successful
            description: Human-readable description
            changes: Summary of changes made
            old_values: Values before change
            new_values: Values after change
            error_message: Error details if failed
            metadata: Additional context data
            session_id: User session ID
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request tracking ID
            
        Returns:
            str: Unique event ID
        """
        
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            timestamp=timestamp,
            user_id=user_id,
            session_id=session_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            level=level,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            changes=changes,
            old_values=old_values,
            new_values=new_values,
            description=description,
            error_message=error_message,
            metadata=metadata
        )
        
        # Calculate integrity checksum
        event.checksum = self._calculate_checksum(event)
        
        # Add to buffer for batch processing
        with self._buffer_lock:
            self._event_buffer.append(event)
            
            # Process batch if buffer is full
            if len(self._event_buffer) >= self._batch_size:
                self._flush_buffer()
        
        # Update statistics
        self._stats["total_events"] += 1
        self._stats[f"action_{action.value}"] += 1
        self._stats[f"level_{level.value}"] += 1
        
        # Log to application logger as well
        log_level = "critical" if level == AuditLevel.CRITICAL else "info"
        getattr(self.logger, log_level)(
            f"AUDIT: {action.value} on {resource_type}#{resource_id or 'unknown'}",
            event_id=event_id,
            user_id=user_id,
            action=action.value,
            resource_type=resource_type,
            success=success
        )
        
        return event_id
    
    def _calculate_checksum(self, event: AuditEvent) -> str:
        """Calculate SHA-256 checksum for event integrity"""
        
        # Create deterministic string representation
        checksum_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "action": event.action.value,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "success": event.success,
            "changes": event.changes,
            "old_values": event.old_values,
            "new_values": event.new_values
        }
        
        # Convert to JSON string with sorted keys for consistency
        json_str = json.dumps(checksum_data, sort_keys=True, default=str)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def _flush_buffer(self):
        """Flush event buffer to database"""
        
        if not self._event_buffer:
            return
        
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as conn:
                # Insert all events in batch
                events_data = []
                for event in self._event_buffer:
                    events_data.append({
                        'event_id': event.event_id,
                        'timestamp': event.timestamp,
                        'user_id': event.user_id,
                        'session_id': event.session_id,
                        'action': event.action.value,
                        'resource_type': event.resource_type,
                        'resource_id': event.resource_id,
                        'level': event.level.value,
                        'success': event.success,
                        'ip_address': event.ip_address,
                        'user_agent': event.user_agent,
                        'request_id': event.request_id,
                        'changes': event.changes,
                        'old_values': event.old_values,
                        'new_values': event.new_values,
                        'description': event.description,
                        'error_message': event.error_message,
                        'metadata': event.metadata,
                        'checksum': event.checksum
                    })
                
                conn.execute(self.audit_table.insert(), events_data)
                conn.commit()
                
                self.logger.info(f"Flushed {len(self._event_buffer)} audit events to database")
                
                # Clear buffer
                self._event_buffer.clear()
                
        except Exception as e:
            self.logger.error(f"Failed to flush audit events: {str(e)}")
            # Keep events in buffer for retry
    
    def force_flush(self):
        """Force flush of all pending events"""
        with self._buffer_lock:
            if self._event_buffer:
                self._flush_buffer()
    
    def search_events(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        level: Optional[AuditLevel] = None,
        success: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search audit events with filters
        
        Args:
            user_id: Filter by user ID
            action: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            level: Filter by audit level
            success: Filter by success status
            start_date: Filter events after this date
            end_date: Filter events before this date
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of audit events
        """
        
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as conn:
                # Build query
                query = self.audit_table.select()
                
                # Add filters
                if user_id:
                    query = query.where(self.audit_table.c.user_id == user_id)
                if action:
                    query = query.where(self.audit_table.c.action == action.value)
                if resource_type:
                    query = query.where(self.audit_table.c.resource_type == resource_type)
                if resource_id:
                    query = query.where(self.audit_table.c.resource_id == resource_id)
                if level:
                    query = query.where(self.audit_table.c.level == level.value)
                if success is not None:
                    query = query.where(self.audit_table.c.success == success)
                if start_date:
                    query = query.where(self.audit_table.c.timestamp >= start_date)
                if end_date:
                    query = query.where(self.audit_table.c.timestamp <= end_date)
                
                # Order by timestamp (newest first)
                query = query.order_by(self.audit_table.c.timestamp.desc())
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                # Execute query
                result = conn.execute(query)
                
                events = []
                for row in result:
                    events.append(dict(row._mapping))
                
                return events
                
        except Exception as e:
            self.logger.error(f"Failed to search audit events: {str(e)}")
            raise create_database_error("DB_QUERY_FAILED", str(e))
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific audit event by ID"""
        
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as conn:
                query = self.audit_table.select().where(
                    self.audit_table.c.event_id == event_id
                )
                
                result = conn.execute(query).fetchone()
                
                if result:
                    return dict(result._mapping)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get audit event {event_id}: {str(e)}")
            raise create_database_error("DB_QUERY_FAILED", str(e))
    
    def verify_event_integrity(self, event_id: str) -> bool:
        """Verify the integrity of an audit event"""
        
        event_data = self.get_event_by_id(event_id)
        if not event_data:
            return False
        
        # Recreate checksum
        stored_checksum = event_data.pop('checksum')
        
        # Convert back to AuditEvent for checksum calculation
        event = AuditEvent(
            event_id=event_data['event_id'],
            timestamp=event_data['timestamp'],
            user_id=event_data['user_id'],
            session_id=event_data['session_id'],
            action=AuditAction(event_data['action']),
            resource_type=event_data['resource_type'],
            resource_id=event_data['resource_id'],
            level=AuditLevel(event_data['level']),
            success=event_data['success'],
            changes=event_data['changes'],
            old_values=event_data['old_values'],
            new_values=event_data['new_values']
        )
        
        calculated_checksum = self._calculate_checksum(event)
        
        return calculated_checksum == stored_checksum
    
    def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit trail statistics"""
        
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as conn:
                # Base query
                base_query = self.audit_table.select()
                
                # Add date filters
                if start_date:
                    base_query = base_query.where(self.audit_table.c.timestamp >= start_date)
                if end_date:
                    base_query = base_query.where(self.audit_table.c.timestamp <= end_date)
                
                # Total events
                total_events = conn.execute(
                    f"SELECT COUNT(*) FROM ({base_query}) as filtered"
                ).scalar()
                
                # Events by action
                action_stats = {}
                for action in AuditAction:
                    count = conn.execute(
                        base_query.where(self.audit_table.c.action == action.value)
                    ).rowcount
                    if count > 0:
                        action_stats[action.value] = count
                
                # Events by level
                level_stats = {}
                for level in AuditLevel:
                    count_query = base_query.where(self.audit_table.c.level == level.value)
                    count = len(list(conn.execute(count_query)))
                    if count > 0:
                        level_stats[level.value] = count
                
                # Success rate
                success_count = len(list(conn.execute(
                    base_query.where(self.audit_table.c.success == True)
                )))
                success_rate = (success_count / total_events * 100) if total_events > 0 else 0
                
                # Most active users
                user_activity_query = f"""
                SELECT user_id, COUNT(*) as event_count 
                FROM ({base_query}) as filtered 
                WHERE user_id IS NOT NULL 
                GROUP BY user_id 
                ORDER BY event_count DESC 
                LIMIT 10
                """
                
                user_activity = []
                try:
                    result = conn.execute(user_activity_query)
                    user_activity = [dict(row._mapping) for row in result]
                except:
                    user_activity = []
                
                return {
                    "period": {
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None
                    },
                    "total_events": total_events,
                    "success_rate_percent": round(success_rate, 2),
                    "events_by_action": action_stats,
                    "events_by_level": level_stats,
                    "most_active_users": user_activity,
                    "buffer_stats": {
                        "pending_events": len(self._event_buffer),
                        "batch_size": self._batch_size
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get audit statistics: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_old_events(self, dry_run: bool = True) -> Dict[str, int]:
        """
        Clean up audit events older than retention period
        
        Args:
            dry_run: If True, only count events without deleting
            
        Returns:
            Dictionary with cleanup results
        """
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as conn:
                # Count events to be deleted
                count_query = self.audit_table.select().where(
                    self.audit_table.c.timestamp < cutoff_date
                )
                events_to_delete = len(list(conn.execute(count_query)))
                
                if dry_run:
                    return {
                        "events_to_delete": events_to_delete,
                        "cutoff_date": cutoff_date.isoformat(),
                        "dry_run": True
                    }
                
                # Delete old events
                delete_query = self.audit_table.delete().where(
                    self.audit_table.c.timestamp < cutoff_date
                )
                
                result = conn.execute(delete_query)
                conn.commit()
                
                deleted_count = result.rowcount
                
                self.logger.info(f"Deleted {deleted_count} old audit events")
                
                return {
                    "events_deleted": deleted_count,
                    "cutoff_date": cutoff_date.isoformat(),
                    "dry_run": False
                }
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup audit events: {str(e)}")
            raise create_database_error("DB_CLEANUP_FAILED", str(e))


# Decorator for automatic audit logging
def audit_action(
    action: AuditAction,
    resource_type: str,
    level: AuditLevel = AuditLevel.MEDIUM,
    capture_args: bool = False
):
    """
    Decorator to automatically audit function calls
    
    Args:
        action: Type of action being performed
        resource_type: Type of resource being affected
        level: Audit level for the action
        capture_args: Whether to capture function arguments
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get audit manager
            if 'audit_manager' in globals():
                audit_manager = globals()['audit_manager']
            else:
                # Skip auditing if manager not available
                return func(*args, **kwargs)
            
            # Extract common parameters
            user_id = kwargs.get('user_id') or getattr(args[0], 'user_id', None) if args else None
            resource_id = kwargs.get('resource_id') or kwargs.get('id')
            
            # Capture arguments if requested
            metadata = {}
            if capture_args:
                metadata['function_args'] = {
                    'args': [str(arg) for arg in args],
                    'kwargs': {k: str(v) for k, v in kwargs.items()}
                }
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log successful action
                audit_manager.log_event(
                    action=action,
                    resource_type=resource_type,
                    user_id=user_id,
                    resource_id=resource_id,
                    level=level,
                    success=True,
                    description=f"Successfully executed {func.__name__}",
                    metadata=metadata
                )
                
                return result
                
            except Exception as e:
                # Log failed action
                audit_manager.log_event(
                    action=action,
                    resource_type=resource_type,
                    user_id=user_id,
                    resource_id=resource_id,
                    level=level,
                    success=False,
                    description=f"Failed to execute {func.__name__}",
                    error_message=str(e),
                    metadata=metadata
                )
                
                # Re-raise exception
                raise
        
        return wrapper
    return decorator


# === GLOBAL INSTANCE ===
audit_manager: Optional[AuditTrailManager] = None


def initialize_audit_system(
    database_url: str,
    retention_days: int = 2555  # 7 years
) -> AuditTrailManager:
    """Initialize the audit trail system"""
    global audit_manager
    
    audit_manager = AuditTrailManager(database_url, retention_days)
    logger = get_logger()
    logger.info(f"Audit trail system initialized with {retention_days} days retention")
    
    return audit_manager


def get_audit_manager() -> AuditTrailManager:
    """Get the global audit manager instance"""
    global audit_manager
    
    if audit_manager is None:
        raise RuntimeError("Audit trail system not initialized")
    
    return audit_manager


# Convenience functions for common audit events
def audit_login(user_id: str, success: bool, ip_address: str = None, error_message: str = None):
    """Audit user login attempt"""
    if audit_manager:
        audit_manager.log_event(
            action=AuditAction.LOGIN,
            resource_type="user_session",
            user_id=user_id,
            level=AuditLevel.MEDIUM,
            success=success,
            description="User login attempt",
            ip_address=ip_address,
            error_message=error_message
        )


def audit_data_change(
    action: AuditAction,
    resource_type: str,
    resource_id: str,
    user_id: str,
    old_values: Dict[str, Any] = None,
    new_values: Dict[str, Any] = None
):
    """Audit data modification"""
    if audit_manager:
        changes = {}
        if old_values and new_values:
            for key in new_values:
                if key in old_values and old_values[key] != new_values[key]:
                    changes[key] = {
                        "from": old_values[key],
                        "to": new_values[key]
                    }
        
        audit_manager.log_event(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            level=AuditLevel.HIGH,
            success=True,
            description=f"Data {action.value} on {resource_type}",
            changes=changes,
            old_values=old_values,
            new_values=new_values
        )