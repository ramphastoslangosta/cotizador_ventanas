# data_protection/retention_policies.py
"""
Data Retention Policies System for Window Quotation System
Milestone 1.3: Data Protection

Features:
- Configurable retention policies for different data types
- Automated cleanup based on age and status
- GDPR compliance with data minimization
- Policy enforcement with logging and auditing
- Grace periods and user notifications
- Compliance reporting
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import schedule
import threading
import time

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from error_handling.logging_config import get_logger
from error_handling.error_manager import create_database_error, create_business_error


class RetentionAction(str, Enum):
    """Actions to take when retention period expires"""
    SOFT_DELETE = "soft_delete"
    HARD_DELETE = "hard_delete"
    ARCHIVE = "archive"
    ANONYMIZE = "anonymize"
    NO_ACTION = "no_action"


class DataCategory(str, Enum):
    """Categories of data for retention policies"""
    USER_PROFILE = "user_profile"
    QUOTES = "quotes"
    MATERIALS = "materials"
    PRODUCTS = "products"
    AUDIT_LOGS = "audit_logs"
    SECURITY_LOGS = "security_logs"
    BACKUPS = "backups"
    EXPORTS = "exports"
    SESSIONS = "sessions"


@dataclass
class RetentionPolicy:
    """Data retention policy configuration"""
    name: str
    data_category: DataCategory
    model_class_name: str
    retention_days: int
    action: RetentionAction
    grace_period_days: int = 7
    enabled: bool = True
    conditions: Dict[str, Any] = None  # Additional conditions for policy application
    description: str = ""
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class RetentionReport:
    """Retention policy execution report"""
    policy_name: str
    execution_date: datetime
    records_evaluated: int
    records_affected: int
    action_taken: RetentionAction
    success: bool
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    details: Dict[str, Any] = None


class DataRetentionManager:
    """
    Manage data retention policies and automated cleanup
    """
    
    def __init__(self):
        self.policies: Dict[str, RetentionPolicy] = {}
        self.logger = get_logger()
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # Load default policies
        self._load_default_policies()
    
    def _load_default_policies(self):
        """Load default retention policies for common data types"""
        
        default_policies = [
            RetentionPolicy(
                name="inactive_user_sessions",
                data_category=DataCategory.SESSIONS,
                model_class_name="UserSession",
                retention_days=30,
                action=RetentionAction.HARD_DELETE,
                grace_period_days=0,
                description="Clean up expired user sessions after 30 days"
            ),
            
            RetentionPolicy(
                name="old_quotes_soft_delete",
                data_category=DataCategory.QUOTES,
                model_class_name="Quote",
                retention_days=365 * 2,  # 2 years
                action=RetentionAction.SOFT_DELETE,
                grace_period_days=30,
                conditions={"status": "draft"},  # Only draft quotes
                description="Soft delete draft quotes older than 2 years"
            ),
            
            RetentionPolicy(
                name="completed_quotes_archive",
                data_category=DataCategory.QUOTES,
                model_class_name="Quote",
                retention_days=365 * 7,  # 7 years for tax purposes
                action=RetentionAction.ARCHIVE,
                grace_period_days=90,
                conditions={"status": "completed"},
                description="Archive completed quotes after 7 years"
            ),
            
            RetentionPolicy(
                name="audit_logs_cleanup",
                data_category=DataCategory.AUDIT_LOGS,
                model_class_name="AuditLog",
                retention_days=365 * 3,  # 3 years
                action=RetentionAction.HARD_DELETE,
                grace_period_days=30,
                description="Delete audit logs after 3 years"
            ),
            
            RetentionPolicy(
                name="security_logs_retention",
                data_category=DataCategory.SECURITY_LOGS,
                model_class_name="SecurityLog",
                retention_days=365 * 2,  # 2 years
                action=RetentionAction.HARD_DELETE,
                grace_period_days=60,
                description="Delete security logs after 2 years"
            ),
            
            RetentionPolicy(
                name="old_backups_cleanup",
                data_category=DataCategory.BACKUPS,
                model_class_name="Backup",
                retention_days=90,  # 3 months
                action=RetentionAction.HARD_DELETE,
                grace_period_days=7,
                description="Delete old database backups after 90 days"
            ),
            
            RetentionPolicy(
                name="export_files_cleanup", 
                data_category=DataCategory.EXPORTS,
                model_class_name="DataExport",
                retention_days=7,  # 1 week
                action=RetentionAction.HARD_DELETE,
                grace_period_days=0,
                description="Delete user data export files after 7 days"
            )
        ]
        
        for policy in default_policies:
            policy.created_at = datetime.utcnow()
            policy.updated_at = datetime.utcnow()
            self.policies[policy.name] = policy
        
        self.logger.info(f"Loaded {len(default_policies)} default retention policies")
    
    def add_policy(self, policy: RetentionPolicy) -> bool:
        """
        Add or update a retention policy
        
        Args:
            policy: RetentionPolicy object
            
        Returns:
            bool: True if successful
        """
        
        try:
            if policy.name in self.policies:
                # Update existing policy
                existing_policy = self.policies[policy.name]
                policy.created_at = existing_policy.created_at
                policy.updated_at = datetime.utcnow()
                
                self.logger.info(f"Updated retention policy: {policy.name}")
            else:
                # Create new policy
                policy.created_at = datetime.utcnow()
                policy.updated_at = datetime.utcnow()
                
                self.logger.info(f"Added new retention policy: {policy.name}")
            
            self.policies[policy.name] = policy
            
            self.logger.audit_event(
                "retention_policy_modified",
                f"policy#{policy.name}",
                result="success",
                action="add_or_update"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add retention policy {policy.name}: {str(e)}")
            return False
    
    def remove_policy(self, policy_name: str) -> bool:
        """
        Remove a retention policy
        
        Args:
            policy_name: Name of policy to remove
            
        Returns:
            bool: True if successful
        """
        
        try:
            if policy_name not in self.policies:
                return False
            
            del self.policies[policy_name]
            
            self.logger.info(f"Removed retention policy: {policy_name}")
            
            self.logger.audit_event(
                "retention_policy_removed",
                f"policy#{policy_name}",
                result="success"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove retention policy {policy_name}: {str(e)}")
            return False
    
    def get_policy(self, policy_name: str) -> Optional[RetentionPolicy]:
        """Get a retention policy by name"""
        return self.policies.get(policy_name)
    
    def list_policies(self) -> List[RetentionPolicy]:
        """List all retention policies"""
        return list(self.policies.values())
    
    def execute_policy(
        self,
        session: Session,
        policy_name: str,
        dry_run: bool = True
    ) -> RetentionReport:
        """
        Execute a specific retention policy
        
        Args:
            session: Database session
            policy_name: Name of policy to execute
            dry_run: If True, only count records without taking action
            
        Returns:
            RetentionReport with execution results
        """
        
        if policy_name not in self.policies:
            raise create_business_error("POLICY_NOT_FOUND", f"Policy: {policy_name}")
        
        policy = self.policies[policy_name]
        
        if not policy.enabled:
            return RetentionReport(
                policy_name=policy_name,
                execution_date=datetime.utcnow(),
                records_evaluated=0,
                records_affected=0,
                action_taken=RetentionAction.NO_ACTION,
                success=True,
                error_message="Policy is disabled"
            )
        
        start_time = time.time()
        
        try:
            self.logger.info(f"Executing retention policy: {policy_name} (dry_run={dry_run})")
            
            # Get model class
            model_class = self._get_model_class(policy.model_class_name)
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
            grace_cutoff_date = cutoff_date - timedelta(days=policy.grace_period_days)
            
            # Build query
            query = self._build_retention_query(session, model_class, policy, grace_cutoff_date)
            
            # Count records that would be affected
            records_evaluated = query.count()
            
            if dry_run:
                return RetentionReport(
                    policy_name=policy_name,
                    execution_date=datetime.utcnow(),
                    records_evaluated=records_evaluated,
                    records_affected=records_evaluated,
                    action_taken=policy.action,
                    success=True,
                    execution_time_seconds=time.time() - start_time,
                    details={
                        "dry_run": True,
                        "cutoff_date": cutoff_date.isoformat(),
                        "grace_cutoff_date": grace_cutoff_date.isoformat()
                    }
                )
            
            # Execute retention action
            records_affected = self._execute_retention_action(
                session, query, policy, model_class
            )
            
            execution_time = time.time() - start_time
            
            report = RetentionReport(
                policy_name=policy_name,
                execution_date=datetime.utcnow(),
                records_evaluated=records_evaluated,
                records_affected=records_affected,
                action_taken=policy.action,
                success=True,
                execution_time_seconds=execution_time,
                details={
                    "dry_run": False,
                    "cutoff_date": cutoff_date.isoformat(),
                    "grace_cutoff_date": grace_cutoff_date.isoformat()
                }
            )
            
            self.logger.info(
                f"Retention policy executed: {policy_name} - {records_affected} records affected"
            )
            
            self.logger.audit_event(
                "retention_policy_executed",
                f"policy#{policy_name}",
                result="success",
                records_affected=records_affected,
                action=policy.action
            )
            
            return report
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            self.logger.error(f"Retention policy execution failed: {policy_name} - {str(e)}")
            
            return RetentionReport(
                policy_name=policy_name,
                execution_date=datetime.utcnow(),
                records_evaluated=0,
                records_affected=0,
                action_taken=RetentionAction.NO_ACTION,
                success=False,
                error_message=str(e),
                execution_time_seconds=execution_time
            )
    
    def _get_model_class(self, model_class_name: str) -> Type:
        """Get SQLAlchemy model class by name"""
        
        # Import here to avoid circular imports
        from database import User, UserSession, Quote, AppMaterial, AppProduct
        
        model_classes = {
            "User": User,
            "UserSession": UserSession,
            "Quote": Quote,
            "AppMaterial": AppMaterial,
            "AppProduct": AppProduct
        }
        
        if model_class_name not in model_classes:
            raise create_business_error("MODEL_NOT_FOUND", f"Model: {model_class_name}")
        
        return model_classes[model_class_name]
    
    def _build_retention_query(
        self,
        session: Session,
        model_class: Type,
        policy: RetentionPolicy,
        cutoff_date: datetime
    ):
        """Build query for records eligible for retention action"""
        
        # Base query with date filter
        if hasattr(model_class, 'created_at'):
            query = session.query(model_class).filter(
                model_class.created_at < cutoff_date
            )
        elif hasattr(model_class, 'updated_at'):
            query = session.query(model_class).filter(
                model_class.updated_at < cutoff_date
            )
        else:
            # Fallback to all records if no date field
            query = session.query(model_class)
        
        # Add soft delete filter if applicable
        if hasattr(model_class, 'is_deleted'):
            if policy.action == RetentionAction.HARD_DELETE:
                # For hard delete, only target soft-deleted records
                query = query.filter(model_class.is_deleted == True)
            else:
                # For other actions, target active records
                query = query.filter(model_class.is_deleted == False)
        
        # Add policy-specific conditions
        if policy.conditions:
            for field, value in policy.conditions.items():
                if hasattr(model_class, field):
                    query = query.filter(getattr(model_class, field) == value)
        
        return query
    
    def _execute_retention_action(
        self,
        session: Session,
        query,
        policy: RetentionPolicy,
        model_class: Type
    ) -> int:
        """Execute the retention action on query results"""
        
        records_affected = 0
        
        if policy.action == RetentionAction.SOFT_DELETE:
            # Soft delete records
            records = query.all()
            for record in records:
                if hasattr(record, 'soft_delete'):
                    record.soft_delete(reason=f"Retention policy: {policy.name}")
                    records_affected += 1
        
        elif policy.action == RetentionAction.HARD_DELETE:
            # Permanently delete records
            records = query.all()
            for record in records:
                session.delete(record)
                records_affected += 1
        
        elif policy.action == RetentionAction.ANONYMIZE:
            # Anonymize personal data
            records = query.all()
            for record in records:
                self._anonymize_record(record)
                records_affected += 1
        
        elif policy.action == RetentionAction.ARCHIVE:
            # Archive records (implementation depends on archival system)
            records = query.all()
            for record in records:
                self._archive_record(record, policy)
                records_affected += 1
        
        # Commit changes
        session.commit()
        
        return records_affected
    
    def _anonymize_record(self, record: Any):
        """Anonymize personal data in a record"""
        
        # Define fields that contain personal data
        personal_fields = [
            'email', 'full_name', 'phone', 'address', 'client_name', 
            'client_email', 'client_phone', 'client_address'
        ]
        
        for field in personal_fields:
            if hasattr(record, field):
                setattr(record, field, f"[ANONYMIZED_{field.upper()}]")
        
        # Mark as anonymized
        if hasattr(record, 'is_anonymized'):
            record.is_anonymized = True
        
        if hasattr(record, 'anonymized_at'):
            record.anonymized_at = datetime.utcnow()
    
    def _archive_record(self, record: Any, policy: RetentionPolicy):
        """Archive a record (placeholder for archival implementation)"""
        
        # This would integrate with your archival system
        # For now, just mark as archived
        if hasattr(record, 'is_archived'):
            record.is_archived = True
        
        if hasattr(record, 'archived_at'):
            record.archived_at = datetime.utcnow()
        
        if hasattr(record, 'archive_policy'):
            record.archive_policy = policy.name
    
    def execute_all_policies(
        self,
        session: Session,
        dry_run: bool = True
    ) -> List[RetentionReport]:
        """
        Execute all enabled retention policies
        
        Args:
            session: Database session
            dry_run: If True, only count records without taking action
            
        Returns:
            List of RetentionReport objects
        """
        
        reports = []
        enabled_policies = [p for p in self.policies.values() if p.enabled]
        
        self.logger.info(f"Executing {len(enabled_policies)} retention policies (dry_run={dry_run})")
        
        for policy in enabled_policies:
            try:
                report = self.execute_policy(session, policy.name, dry_run)
                reports.append(report)
            except Exception as e:
                self.logger.error(f"Failed to execute policy {policy.name}: {str(e)}")
                reports.append(RetentionReport(
                    policy_name=policy.name,
                    execution_date=datetime.utcnow(),
                    records_evaluated=0,
                    records_affected=0,
                    action_taken=RetentionAction.NO_ACTION,
                    success=False,
                    error_message=str(e)
                ))
        
        # Generate summary
        total_affected = sum(r.records_affected for r in reports if r.success)
        successful = len([r for r in reports if r.success])
        
        self.logger.info(
            f"Retention policy execution complete: {successful}/{len(reports)} policies successful, {total_affected} records affected"
        )
        
        return reports
    
    def get_retention_status(self, session: Session) -> Dict[str, Any]:
        """
        Get current retention status across all policies
        
        Args:
            session: Database session
            
        Returns:
            Dictionary with retention status information
        """
        
        try:
            status = {
                "total_policies": len(self.policies),
                "enabled_policies": len([p for p in self.policies.values() if p.enabled]),
                "policies": {},
                "summary": {
                    "total_records_eligible": 0,
                    "by_action": {action.value: 0 for action in RetentionAction}
                }
            }
            
            for policy_name, policy in self.policies.items():
                if not policy.enabled:
                    status["policies"][policy_name] = {
                        "enabled": False,
                        "records_eligible": 0
                    }
                    continue
                
                try:
                    # Get dry run report
                    report = self.execute_policy(session, policy_name, dry_run=True)
                    
                    status["policies"][policy_name] = {
                        "enabled": True,
                        "records_eligible": report.records_affected,
                        "action": policy.action.value,
                        "retention_days": policy.retention_days,
                        "grace_period_days": policy.grace_period_days
                    }
                    
                    status["summary"]["total_records_eligible"] += report.records_affected
                    status["summary"]["by_action"][policy.action.value] += report.records_affected
                    
                except Exception as e:
                    status["policies"][policy_name] = {
                        "enabled": True,
                        "error": str(e)
                    }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get retention status: {str(e)}")
            return {"error": str(e)}
    
    def start_scheduled_retention(self, run_time: str = "03:00"):
        """
        Start scheduled retention policy execution
        
        Args:
            run_time: Time to run daily retention (HH:MM format)
        """
        
        if self.scheduler_running:
            self.logger.warning("Retention scheduler is already running")
            return
        
        # Schedule daily retention at specified time
        schedule.every().day.at(run_time).do(self._scheduled_retention)
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info(f"Retention scheduler started: daily at {run_time}")
    
    def stop_scheduled_retention(self):
        """Stop scheduled retention execution"""
        
        self.scheduler_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Retention scheduler stopped")
    
    def _run_scheduler(self):
        """Run the retention scheduler in background thread"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _scheduled_retention(self):
        """Execute scheduled retention policies"""
        try:
            # This would need a database session from the application
            # For now, just log that retention should run
            self.logger.info("Scheduled retention execution triggered")
            
            # In a real implementation, you'd:
            # 1. Get a database session
            # 2. Execute retention policies
            # 3. Generate compliance reports
            
        except Exception as e:
            self.logger.error(f"Scheduled retention failed: {str(e)}")


# === GLOBAL INSTANCE ===
retention_manager: Optional[DataRetentionManager] = None


def initialize_retention_system() -> DataRetentionManager:
    """Initialize the data retention system"""
    global retention_manager
    
    retention_manager = DataRetentionManager()
    logger = get_logger()
    logger.info("Data retention system initialized")
    
    return retention_manager


def get_retention_manager() -> DataRetentionManager:
    """Get the global retention manager instance"""
    global retention_manager
    
    if retention_manager is None:
        raise RuntimeError("Data retention system not initialized")
    
    return retention_manager