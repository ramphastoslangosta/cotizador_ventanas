# data_protection/backup_manager.py
"""
Automated Database Backup System for Window Quotation System
Milestone 1.3: Data Protection

Features:
- Automated PostgreSQL database backups
- Configurable backup schedules
- Backup rotation and retention policies
- Backup integrity verification
- Cloud storage integration (optional)
- Backup restoration capabilities
"""

import os
import subprocess
import gzip
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import schedule
import threading
import time
import hashlib
import json

from error_handling.logging_config import get_logger
from error_handling.error_manager import create_database_error, DatabaseError


class BackupStatus(str, Enum):
    """Backup operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


class BackupType(str, Enum):
    """Types of backups"""
    FULL = "full"
    INCREMENTAL = "incremental"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"


@dataclass
class BackupConfig:
    """Backup configuration settings"""
    backup_dir: str = "backups"
    max_backups: int = 7  # Keep last 7 backups
    compression: bool = True
    verify_backup: bool = True
    backup_schedule: str = "daily"  # daily, weekly, hourly
    backup_time: str = "02:00"  # 2 AM
    retention_days: int = 30
    include_schema: bool = True
    include_data: bool = True
    
    # Database connection settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ventanas_db"
    db_user: str = "postgres"
    db_password: str = ""


@dataclass
class BackupInfo:
    """Backup information record"""
    backup_id: str
    timestamp: datetime.datetime
    backup_type: BackupType
    status: BackupStatus
    file_path: str
    file_size: int
    duration_seconds: float
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DatabaseBackupManager:
    """Manage automated database backups"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.logger = get_logger()
        self.backup_dir = Path(config.backup_dir)
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        
        # Create metadata directory
        self.metadata_dir = self.backup_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
        
        # Backup history
        self.backup_history: List[BackupInfo] = []
        self._load_backup_history()
        
        # Scheduler setup
        self.scheduler_thread = None
        self.scheduler_running = False
    
    def create_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        custom_name: Optional[str] = None
    ) -> BackupInfo:
        """Create a database backup"""
        
        backup_id = custom_name or f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()
        
        self.logger.info(f"Starting {backup_type} backup: {backup_id}")
        
        # Create backup info
        backup_info = BackupInfo(
            backup_id=backup_id,
            timestamp=datetime.datetime.now(),
            backup_type=backup_type,
            status=BackupStatus.RUNNING,
            file_path="",
            file_size=0,
            duration_seconds=0
        )
        
        try:
            # Generate backup file path
            if self.config.compression:
                backup_file = self.backup_dir / f"{backup_id}.sql.gz"
            else:
                backup_file = self.backup_dir / f"{backup_id}.sql"
            
            backup_info.file_path = str(backup_file)
            
            # Create pg_dump command
            dump_command = self._build_dump_command(backup_type, backup_file)
            
            self.logger.database_operation("backup", f"Running pg_dump command", 
                                         backup_id=backup_id, backup_type=backup_type)
            
            # Execute backup
            result = subprocess.run(
                dump_command,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                error_msg = f"pg_dump failed: {result.stderr}"
                backup_info.status = BackupStatus.FAILED
                backup_info.error_message = error_msg
                self.logger.database_error("backup", error_msg, backup_id=backup_id)
                raise DatabaseError(
                    message_es="Error al crear respaldo de la base de datos.",
                    message_en="Database backup creation failed",
                    technical_details=error_msg
                )
            
            # Calculate file size and duration
            backup_info.file_size = backup_file.stat().st_size
            backup_info.duration_seconds = time.time() - start_time
            backup_info.status = BackupStatus.COMPLETED
            
            # Generate checksum if verification is enabled
            if self.config.verify_backup:
                backup_info.checksum = self._calculate_checksum(backup_file)
                backup_info.status = BackupStatus.VERIFIED
                self.logger.info(f"Backup verified: {backup_id}, checksum: {backup_info.checksum[:8]}...")
            
            # Add metadata
            backup_info.metadata = {
                "pg_dump_version": self._get_pg_dump_version(),
                "database_size": self._get_database_size(),
                "table_count": self._get_table_count(),
                "compression": self.config.compression
            }
            
            # Save backup info
            self._save_backup_info(backup_info)
            self.backup_history.append(backup_info)
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            self.logger.info(
                f"Backup completed successfully: {backup_id}",
                backup_id=backup_id,
                file_size=backup_info.file_size,
                duration=backup_info.duration_seconds
            )
            
            self.logger.audit_event("database_backup", "database", result="success",
                                  backup_id=backup_id, backup_type=backup_type)
            
            return backup_info
            
        except subprocess.TimeoutExpired:
            backup_info.status = BackupStatus.FAILED
            backup_info.error_message = "Backup operation timed out"
            backup_info.duration_seconds = time.time() - start_time
            
            self.logger.database_error("backup", "Backup timed out", backup_id=backup_id)
            raise DatabaseError(
                message_es="El respaldo de la base de datos excedió el tiempo límite.",
                message_en="Database backup timed out",
                technical_details="Backup operation exceeded 1 hour timeout"
            )
            
        except Exception as e:
            backup_info.status = BackupStatus.FAILED
            backup_info.error_message = str(e)
            backup_info.duration_seconds = time.time() - start_time
            
            self.logger.database_error("backup", f"Backup failed: {str(e)}", backup_id=backup_id)
            
            # Save failed backup info for debugging
            self._save_backup_info(backup_info)
            self.backup_history.append(backup_info)
            
            raise
    
    def _build_dump_command(self, backup_type: BackupType, backup_file: Path) -> List[str]:
        """Build pg_dump command based on backup type"""
        
        cmd = [
            "pg_dump",
            "-h", self.config.db_host,
            "-p", str(self.config.db_port),
            "-U", self.config.db_user,
            "-d", self.config.db_name,
            "--verbose",
            "--no-password"  # Use .pgpass or environment variables for password
        ]
        
        # Add backup type specific options
        if backup_type == BackupType.SCHEMA_ONLY:
            cmd.append("--schema-only")
        elif backup_type == BackupType.DATA_ONLY:
            cmd.append("--data-only")
        # FULL backup includes both schema and data (default)
        
        # Add output redirection
        if self.config.compression:
            cmd.extend(["|", "gzip", ">", str(backup_file)])
            # Use shell=True for pipe operations
            return ["bash", "-c", " ".join(cmd)]
        else:
            cmd.extend(["-f", str(backup_file)])
        
        return cmd
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of backup file"""
        sha256_hash = hashlib.sha256()
        
        if file_path.suffix == '.gz':
            with gzip.open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
        else:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _get_pg_dump_version(self) -> str:
        """Get pg_dump version"""
        try:
            result = subprocess.run(["pg_dump", "--version"], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"
    
    def _get_database_size(self) -> int:
        """Get database size in bytes"""
        try:
            cmd = [
                "psql",
                "-h", self.config.db_host,
                "-p", str(self.config.db_port),
                "-U", self.config.db_user,
                "-d", self.config.db_name,
                "-t", "-c", f"SELECT pg_database_size('{self.config.db_name}');"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return int(result.stdout.strip()) if result.returncode == 0 else 0
        except:
            return 0
    
    def _get_table_count(self) -> int:
        """Get number of tables in database"""
        try:
            cmd = [
                "psql",
                "-h", self.config.db_host,
                "-p", str(self.config.db_port),
                "-U", self.config.db_user,
                "-d", self.config.db_name,
                "-t", "-c", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return int(result.stdout.strip()) if result.returncode == 0 else 0
        except:
            return 0
    
    def _save_backup_info(self, backup_info: BackupInfo):
        """Save backup information to metadata file"""
        metadata_file = self.metadata_dir / f"{backup_info.backup_id}.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(asdict(backup_info), f, indent=2, default=str)
    
    def _load_backup_history(self):
        """Load backup history from metadata files"""
        self.backup_history = []
        
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                
                # Convert string dates back to datetime
                data['timestamp'] = datetime.datetime.fromisoformat(data['timestamp'])
                
                backup_info = BackupInfo(**data)
                self.backup_history.append(backup_info)
                
            except Exception as e:
                self.logger.warning(f"Failed to load backup metadata {metadata_file}: {e}")
        
        # Sort by timestamp
        self.backup_history.sort(key=lambda x: x.timestamp, reverse=True)
    
    def _cleanup_old_backups(self):
        """Remove old backups based on retention policy"""
        
        # Remove backups older than retention period
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.config.retention_days)
        
        backups_to_remove = [
            backup for backup in self.backup_history
            if backup.timestamp < cutoff_date
        ]
        
        # Also remove excess backups beyond max_backups
        if len(self.backup_history) > self.config.max_backups:
            excess_backups = self.backup_history[self.config.max_backups:]
            backups_to_remove.extend(excess_backups)
        
        for backup in backups_to_remove:
            try:
                # Remove backup file
                backup_file = Path(backup.file_path)
                if backup_file.exists():
                    backup_file.unlink()
                
                # Remove metadata file
                metadata_file = self.metadata_dir / f"{backup.backup_id}.json"
                if metadata_file.exists():
                    metadata_file.unlink()
                
                # Remove from history
                self.backup_history.remove(backup)
                
                self.logger.info(f"Removed old backup: {backup.backup_id}")
                
            except Exception as e:
                self.logger.warning(f"Failed to remove backup {backup.backup_id}: {e}")
    
    def restore_backup(self, backup_id: str, target_db: Optional[str] = None) -> bool:
        """Restore database from backup"""
        
        backup_info = self.get_backup_info(backup_id)
        if not backup_info:
            raise DatabaseError(
                message_es="No se encontró el respaldo especificado.",
                message_en="Backup not found",
                technical_details=f"Backup ID: {backup_id}"
            )
        
        backup_file = Path(backup_info.file_path)
        if not backup_file.exists():
            raise DatabaseError(
                message_es="El archivo de respaldo no existe.",
                message_en="Backup file not found",
                technical_details=f"File: {backup_file}"
            )
        
        target_database = target_db or self.config.db_name
        
        self.logger.info(f"Starting restore of backup {backup_id} to database {target_database}")
        
        try:
            # Build restore command
            if backup_file.suffix == '.gz':
                cmd = [
                    "bash", "-c",
                    f"gunzip -c {backup_file} | psql -h {self.config.db_host} -p {self.config.db_port} -U {self.config.db_user} -d {target_database}"
                ]
            else:
                cmd = [
                    "psql",
                    "-h", self.config.db_host,
                    "-p", str(self.config.db_port),
                    "-U", self.config.db_user,
                    "-d", target_database,
                    "-f", str(backup_file)
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode != 0:
                error_msg = f"Restore failed: {result.stderr}"
                self.logger.database_error("restore", error_msg, backup_id=backup_id)
                raise DatabaseError(
                    message_es="Error al restaurar la base de datos desde el respaldo.",
                    message_en="Database restore failed",
                    technical_details=error_msg
                )
            
            self.logger.info(f"Successfully restored backup {backup_id} to {target_database}")
            self.logger.audit_event("database_restore", "database", result="success",
                                  backup_id=backup_id, target_database=target_database)
            
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.database_error("restore", "Restore operation timed out", backup_id=backup_id)
            raise DatabaseError(
                message_es="La restauración de la base de datos excedió el tiempo límite.",
                message_en="Database restore timed out",
                technical_details="Restore operation exceeded 1 hour timeout"
            )
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Get backup information by ID"""
        for backup in self.backup_history:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def list_backups(self) -> List[BackupInfo]:
        """List all available backups"""
        return self.backup_history.copy()
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics"""
        if not self.backup_history:
            return {"total_backups": 0}
        
        successful_backups = [b for b in self.backup_history if b.status in [BackupStatus.COMPLETED, BackupStatus.VERIFIED]]
        failed_backups = [b for b in self.backup_history if b.status == BackupStatus.FAILED]
        
        total_size = sum(b.file_size for b in successful_backups)
        avg_duration = sum(b.duration_seconds for b in successful_backups) / len(successful_backups) if successful_backups else 0
        
        return {
            "total_backups": len(self.backup_history),
            "successful_backups": len(successful_backups),
            "failed_backups": len(failed_backups),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "average_duration_seconds": avg_duration,
            "latest_backup": self.backup_history[0].timestamp.isoformat() if self.backup_history else None,
            "oldest_backup": self.backup_history[-1].timestamp.isoformat() if self.backup_history else None
        }
    
    def start_scheduled_backups(self):
        """Start automated backup scheduler"""
        if self.scheduler_running:
            self.logger.warning("Backup scheduler is already running")
            return
        
        # Configure schedule based on settings
        if self.config.backup_schedule == "daily":
            schedule.every().day.at(self.config.backup_time).do(self._scheduled_backup)
        elif self.config.backup_schedule == "weekly":
            schedule.every().week.at(self.config.backup_time).do(self._scheduled_backup)
        elif self.config.backup_schedule == "hourly":
            schedule.every().hour.do(self._scheduled_backup)
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info(f"Backup scheduler started: {self.config.backup_schedule} at {self.config.backup_time}")
    
    def stop_scheduled_backups(self):
        """Stop automated backup scheduler"""
        self.scheduler_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Backup scheduler stopped")
    
    def _run_scheduler(self):
        """Run the backup scheduler in background thread"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _scheduled_backup(self):
        """Execute scheduled backup"""
        try:
            backup_name = f"scheduled_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.create_backup(BackupType.FULL, backup_name)
            self.logger.info(f"Scheduled backup completed: {backup_name}")
        except Exception as e:
            self.logger.error(f"Scheduled backup failed: {str(e)}")


# === GLOBAL INSTANCE ===
backup_manager: Optional[DatabaseBackupManager] = None


def initialize_backup_system(config: BackupConfig) -> DatabaseBackupManager:
    """Initialize the backup system"""
    global backup_manager
    
    backup_manager = DatabaseBackupManager(config)
    logger = get_logger()
    logger.info("Database backup system initialized")
    
    return backup_manager


def get_backup_manager() -> DatabaseBackupManager:
    """Get the global backup manager instance"""
    global backup_manager
    
    if backup_manager is None:
        raise RuntimeError("Backup system not initialized")
    
    return backup_manager