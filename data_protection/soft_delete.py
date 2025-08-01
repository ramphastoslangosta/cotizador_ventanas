# data_protection/soft_delete.py
"""
Soft Delete System for Window Quotation System
Milestone 1.3: Data Protection

Features:
- Soft delete functionality to prevent accidental data loss
- Automatic restoration capabilities
- Configurable retention periods for soft-deleted records
- Batch operations for cleanup
- Integration with existing models
- Audit trail for delete/restore operations
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Type, Any, Dict
from sqlalchemy import Column, Boolean, DateTime, String, text, and_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect

from error_handling.logging_config import get_logger
from error_handling.error_manager import create_database_error, DatabaseError


class SoftDeleteMixin:
    """
    Mixin class to add soft delete functionality to SQLAlchemy models
    """
    
    @declared_attr
    def is_deleted(cls):
        """Flag to indicate if record is soft deleted"""
        return Column(Boolean, default=False, nullable=False, index=True)
    
    @declared_attr
    def deleted_at(cls):
        """Timestamp when record was soft deleted"""
        return Column(DateTime, nullable=True, index=True)
    
    @declared_attr
    def deleted_by(cls):
        """User ID who performed the soft delete"""
        return Column(String(36), nullable=True)
    
    @declared_attr
    def delete_reason(cls):
        """Reason for deletion (optional)"""
        return Column(String(500), nullable=True)
    
    def soft_delete(self, user_id: str = None, reason: str = None):
        """Soft delete this record"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id
        self.delete_reason = reason
    
    def restore(self):
        """Restore this soft deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.delete_reason = None
    
    @classmethod
    def get_active_query(cls, session: Session):
        """Get query for active (non-deleted) records"""
        return session.query(cls).filter(cls.is_deleted == False)
    
    @classmethod
    def get_deleted_query(cls, session: Session):
        """Get query for soft deleted records"""
        return session.query(cls).filter(cls.is_deleted == True)
    
    @classmethod
    def get_all_query(cls, session: Session):
        """Get query for all records (including soft deleted)"""
        return session.query(cls)


class SoftDeleteManager:
    """
    Manager class for soft delete operations
    """
    
    def __init__(self, retention_days: int = 90):
        """
        Initialize soft delete manager
        
        Args:
            retention_days: Days to keep soft deleted records before permanent deletion
        """
        self.retention_days = retention_days
        self.logger = get_logger()
    
    def soft_delete_record(
        self,
        session: Session,
        model_class: Type,
        record_id: Any,
        user_id: str = None,
        reason: str = None
    ) -> bool:
        """
        Soft delete a single record
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
            record_id: ID of record to delete
            user_id: User performing the deletion
            reason: Reason for deletion
            
        Returns:
            bool: True if successful, False if record not found
        """
        
        try:
            # Get the record
            record = session.query(model_class).filter(
                model_class.id == record_id,
                model_class.is_deleted == False
            ).first()
            
            if not record:
                self.logger.warning(
                    f"Record not found for soft delete: {model_class.__name__}#{record_id}"
                )
                return False
            
            # Perform soft delete
            record.soft_delete(user_id=user_id, reason=reason)
            session.commit()
            
            # Log the operation
            self.logger.audit_event(
                "soft_delete",
                f"{model_class.__name__}#{record_id}",
                user_id=user_id,
                result="success",
                reason=reason
            )
            
            self.logger.info(
                f"Soft deleted {model_class.__name__}#{record_id}",
                model=model_class.__name__,
                record_id=str(record_id),
                user_id=user_id,
                reason=reason
            )
            
            return True
            
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Failed to soft delete {model_class.__name__}#{record_id}: {str(e)}"
            )
            raise create_database_error("DB_TRANSACTION_FAILED", str(e))
    
    def restore_record(
        self,
        session: Session,
        model_class: Type,
        record_id: Any,
        user_id: str = None
    ) -> bool:
        """
        Restore a soft deleted record
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
            record_id: ID of record to restore
            user_id: User performing the restoration
            
        Returns:
            bool: True if successful, False if record not found
        """
        
        try:
            # Get the soft deleted record
            record = session.query(model_class).filter(
                model_class.id == record_id,
                model_class.is_deleted == True
            ).first()
            
            if not record:
                self.logger.warning(
                    f"Soft deleted record not found for restore: {model_class.__name__}#{record_id}"
                )
                return False
            
            # Restore the record
            record.restore()
            session.commit()
            
            # Log the operation
            self.logger.audit_event(
                "restore_record",
                f"{model_class.__name__}#{record_id}",
                user_id=user_id,
                result="success"
            )
            
            self.logger.info(
                f"Restored {model_class.__name__}#{record_id}",
                model=model_class.__name__,
                record_id=str(record_id),
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            session.rollback()
            self.logger.error(
                f"Failed to restore {model_class.__name__}#{record_id}: {str(e)}"
            )
            raise create_database_error("DB_TRANSACTION_FAILED", str(e))
    
    def batch_soft_delete(
        self,
        session: Session,
        model_class: Type,
        record_ids: List[Any],
        user_id: str = None,
        reason: str = None
    ) -> Dict[str, int]:
        """
        Soft delete multiple records in batch
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
            record_ids: List of record IDs to delete
            user_id: User performing the deletion
            reason: Reason for deletion
            
        Returns:
            Dict with success and failure counts
        """
        
        results = {"success": 0, "failed": 0, "not_found": 0}
        
        try:
            for record_id in record_ids:
                try:
                    if self.soft_delete_record(session, model_class, record_id, user_id, reason):
                        results["success"] += 1
                    else:
                        results["not_found"] += 1
                except Exception:
                    results["failed"] += 1
            
            self.logger.info(
                f"Batch soft delete completed for {model_class.__name__}: {results}"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch soft delete failed: {str(e)}")
            raise create_database_error("DB_TRANSACTION_FAILED", str(e))
    
    def get_soft_deleted_records(
        self,
        session: Session,
        model_class: Type,
        limit: int = 100,
        offset: int = 0
    ) -> List[Any]:
        """
        Get list of soft deleted records
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of soft deleted records
        """
        
        try:
            records = session.query(model_class).filter(
                model_class.is_deleted == True
            ).order_by(model_class.deleted_at.desc()).offset(offset).limit(limit).all()
            
            return records
            
        except Exception as e:
            self.logger.error(f"Failed to get soft deleted records: {str(e)}")
            raise create_database_error("DB_QUERY_FAILED", str(e))
    
    def get_deletion_statistics(
        self,
        session: Session,
        model_class: Type
    ) -> Dict[str, Any]:
        """
        Get statistics about deletions for a model
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
            
        Returns:
            Dictionary with deletion statistics
        """
        
        try:
            # Count active records
            active_count = session.query(model_class).filter(
                model_class.is_deleted == False
            ).count()
            
            # Count soft deleted records
            deleted_count = session.query(model_class).filter(
                model_class.is_deleted == True
            ).count()
            
            # Count records eligible for permanent deletion
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            expired_count = session.query(model_class).filter(
                and_(
                    model_class.is_deleted == True,
                    model_class.deleted_at < cutoff_date
                )
            ).count()
            
            # Get recent deletions (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_deletions = session.query(model_class).filter(
                and_(
                    model_class.is_deleted == True,
                    model_class.deleted_at >= recent_cutoff
                )
            ).count()
            
            return {
                "model": model_class.__name__,
                "active_records": active_count,
                "soft_deleted_records": deleted_count,
                "expired_records": expired_count,
                "recent_deletions_7_days": recent_deletions,
                "total_records": active_count + deleted_count,
                "retention_days": self.retention_days
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get deletion statistics: {str(e)}")
            raise create_database_error("DB_QUERY_FAILED", str(e))
    
    def cleanup_expired_records(
        self,
        session: Session,
        model_class: Type,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Permanently delete records that have exceeded retention period
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
            dry_run: If True, only count records without deleting
            
        Returns:
            Dictionary with cleanup results
        """
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            # Find expired records
            expired_records = session.query(model_class).filter(
                and_(
                    model_class.is_deleted == True,
                    model_class.deleted_at < cutoff_date
                )
            ).all()
            
            if dry_run:
                return {
                    "model": model_class.__name__,
                    "expired_count": len(expired_records),
                    "cutoff_date": cutoff_date.isoformat(),
                    "dry_run": True
                }
            
            # Permanently delete expired records
            deleted_count = 0
            for record in expired_records:
                try:
                    session.delete(record)
                    deleted_count += 1
                    
                    # Log each permanent deletion
                    self.logger.audit_event(
                        "permanent_delete",
                        f"{model_class.__name__}#{record.id}",
                        result="success",
                        reason="retention_period_expired"
                    )
                    
                except Exception as e:
                    self.logger.error(
                        f"Failed to permanently delete {model_class.__name__}#{record.id}: {str(e)}"
                    )
            
            session.commit()
            
            self.logger.info(
                f"Permanently deleted {deleted_count} expired {model_class.__name__} records"
            )
            
            return {
                "model": model_class.__name__,
                "expired_count": len(expired_records),
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat(),
                "dry_run": False
            }
            
        except Exception as e:
            session.rollback()
            self.logger.error(f"Failed to cleanup expired records: {str(e)}")
            raise create_database_error("DB_TRANSACTION_FAILED", str(e))
    
    def batch_cleanup_all_models(
        self,
        session: Session,
        model_classes: List[Type],
        dry_run: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Cleanup expired records for multiple models
        
        Args:
            session: Database session
            model_classes: List of SQLAlchemy model classes
            dry_run: If True, only count records without deleting
            
        Returns:
            List of cleanup results for each model
        """
        
        results = []
        
        for model_class in model_classes:
            try:
                result = self.cleanup_expired_records(session, model_class, dry_run)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"Failed to cleanup {model_class.__name__}: {str(e)}"
                )
                results.append({
                    "model": model_class.__name__,
                    "error": str(e),
                    "dry_run": dry_run
                })
        
        return results


# Decorator for automatic soft delete query filtering
def exclude_soft_deleted(func):
    """
    Decorator to automatically filter out soft deleted records from queries
    """
    def wrapper(*args, **kwargs):
        # This is a placeholder - in practice, you'd implement query filtering
        # based on your specific ORM setup
        return func(*args, **kwargs)
    return wrapper


# === GLOBAL INSTANCE ===
soft_delete_manager: Optional[SoftDeleteManager] = None


def initialize_soft_delete_system(retention_days: int = 90) -> SoftDeleteManager:
    """Initialize the soft delete system"""
    global soft_delete_manager
    
    soft_delete_manager = SoftDeleteManager(retention_days)
    logger = get_logger()
    logger.info(f"Soft delete system initialized with {retention_days} days retention")
    
    return soft_delete_manager


def get_soft_delete_manager() -> SoftDeleteManager:
    """Get the global soft delete manager instance"""
    global soft_delete_manager
    
    if soft_delete_manager is None:
        raise RuntimeError("Soft delete system not initialized")
    
    return soft_delete_manager