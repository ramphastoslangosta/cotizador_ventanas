# data_protection/migration_manager.py
"""
Database Migration Manager for Window Quotation System
Milestone 1.3: Data Protection

Features:
- Alembic integration for schema migrations
- Safe migration execution with rollback capabilities
- Migration testing and validation
- Automated backup before migrations
- Migration history tracking
- Production-safe migration procedures
"""

import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import tempfile

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from error_handling.logging_config import get_logger
from error_handling.error_manager import create_database_error, DatabaseError


class MigrationStatus(str, Enum):
    """Migration execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MigrationInfo:
    """Migration information"""
    revision_id: str
    description: str
    upgrade_revision: Optional[str] = None
    downgrade_revision: Optional[str] = None
    created_at: Optional[datetime] = None
    is_applied: bool = False


@dataclass
class MigrationExecution:
    """Migration execution record"""
    execution_id: str
    revision_id: str
    operation: str  # upgrade, downgrade
    status: MigrationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    backup_path: Optional[str] = None
    error_message: Optional[str] = None
    rollback_available: bool = False


class DatabaseMigrationManager:
    """
    Manage database schema migrations safely
    """
    
    def __init__(
        self,
        database_url: str,
        alembic_config_path: str = "alembic.ini",
        migrations_dir: str = "alembic"
    ):
        """
        Initialize migration manager
        
        Args:
            database_url: Database connection URL
            alembic_config_path: Path to Alembic configuration file
            migrations_dir: Directory containing migration files
        """
        self.database_url = database_url
        self.alembic_config_path = Path(alembic_config_path)
        self.migrations_dir = Path(migrations_dir)
        self.logger = get_logger()
        
        # Initialize Alembic if not already done
        self._ensure_alembic_initialized()
        
        # Migration execution history
        self.execution_history: List[MigrationExecution] = []
    
    def _ensure_alembic_initialized(self):
        """Ensure Alembic is properly initialized"""
        
        try:
            # Check if alembic.ini exists
            if not self.alembic_config_path.exists():
                self._create_alembic_config()
            
            # Check if alembic directory exists
            if not self.migrations_dir.exists():
                self._initialize_alembic()
            
            self.logger.info("Alembic migration environment verified")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Alembic: {str(e)}")
            raise create_database_error("MIGRATION_INIT_FAILED", str(e))
    
    def _create_alembic_config(self):
        """Create Alembic configuration file"""
        
        alembic_ini_content = f"""# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = {self.migrations_dir}

# template used to generate migration files
# file_template = %%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date
# within the migration file as well as the filename.
# string value is passed to dateutil.tz.gettz()
# leave blank for localtime
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version file format.   This is the default format used
# for the revision file name, and is configurable.
# version_file_format = %%(rev)s_%%(slug)s

# version path separator
# version_path_separator = os  # default: use os.pathsep

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = {self.database_url}


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %%(levelname)-5.5s [%%(name)s] %%(message)s
datefmt = %%H:%%M:%%S
"""
        
        with open(self.alembic_config_path, 'w') as f:
            f.write(alembic_ini_content)
        
        self.logger.info(f"Created Alembic configuration: {self.alembic_config_path}")
    
    def _initialize_alembic(self):
        """Initialize Alembic migration environment"""
        
        try:
            # Initialize Alembic
            command.init(Config(str(self.alembic_config_path)), str(self.migrations_dir))
            
            # Update env.py to work with our database models
            env_py_path = self.migrations_dir / "env.py"
            self._update_env_py(env_py_path)
            
            self.logger.info("Alembic migration environment initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Alembic: {str(e)}")
            raise
    
    def _update_env_py(self, env_py_path: Path):
        """Update env.py to work with our models"""
        
        env_py_content = '''"""Database migration environment configuration"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import all models for autogenerate support
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import Base  # Import your Base from database.py

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        
        with open(env_py_path, 'w') as f:
            f.write(env_py_content)
        
        self.logger.info("Updated env.py for model integration")
    
    def get_current_revision(self) -> Optional[str]:
        """Get current database revision"""
        
        try:
            config = Config(str(self.alembic_config_path))
            
            # Get current revision from database
            engine = create_engine(self.database_url)
            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()
            
            return current_rev
            
        except Exception as e:
            self.logger.error(f"Failed to get current revision: {str(e)}")
            return None
    
    def get_migration_history(self) -> List[MigrationInfo]:
        """Get list of all available migrations"""
        
        try:
            config = Config(str(self.alembic_config_path))
            script = ScriptDirectory.from_config(config)
            
            migrations = []
            current_rev = self.get_current_revision()
            
            for revision in script.walk_revisions():
                migration = MigrationInfo(
                    revision_id=revision.revision,
                    description=revision.doc or "No description",
                    upgrade_revision=revision.up_revision,
                    downgrade_revision=revision.down_revision,
                    is_applied=(revision.revision == current_rev or 
                              (current_rev and script.get_revision(current_rev) and
                               revision.revision in [r.revision for r in 
                                                   script.walk_revisions(upper=current_rev, lower="base")]))
                )
                migrations.append(migration)
            
            return migrations
            
        except Exception as e:
            self.logger.error(f"Failed to get migration history: {str(e)}")
            return []
    
    def create_migration(
        self,
        message: str,
        autogenerate: bool = True
    ) -> Optional[str]:
        """
        Create a new migration
        
        Args:
            message: Migration description
            autogenerate: Whether to auto-generate migration from model changes
            
        Returns:
            str: New revision ID if successful
        """
        
        try:
            config = Config(str(self.alembic_config_path))
            
            # Create revision
            if autogenerate:
                revision = command.revision(
                    config,
                    message=message,
                    autogenerate=True
                )
            else:
                revision = command.revision(
                    config,
                    message=message
                )
            
            self.logger.info(f"Created migration: {revision.revision} - {message}")
            
            self.logger.audit_event(
                "migration_created",
                f"migration#{revision.revision}",
                result="success",
                message=message,
                autogenerate=autogenerate
            )
            
            return revision.revision
            
        except Exception as e:
            self.logger.error(f"Failed to create migration: {str(e)}")
            raise create_database_error("MIGRATION_CREATE_FAILED", str(e))
    
    def upgrade_database(
        self,
        revision: str = "head",
        create_backup: bool = True
    ) -> MigrationExecution:
        """
        Upgrade database to specified revision
        
        Args:
            revision: Target revision (default: "head")
            create_backup: Whether to create backup before migration
            
        Returns:
            MigrationExecution: Execution record
        """
        
        execution_id = f"upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        execution = MigrationExecution(
            execution_id=execution_id,
            revision_id=revision,
            operation="upgrade",
            status=MigrationStatus.PENDING,
            started_at=datetime.utcnow()
        )
        
        try:
            execution.status = MigrationStatus.RUNNING
            self.execution_history.append(execution)
            
            self.logger.info(f"Starting database upgrade to {revision}")
            
            # Create backup if requested
            if create_backup:
                execution.backup_path = self._create_pre_migration_backup()
                execution.rollback_available = True
            
            # Execute upgrade
            config = Config(str(self.alembic_config_path))
            command.upgrade(config, revision)
            
            # Mark as completed
            execution.status = MigrationStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            
            self.logger.info(f"Database upgrade completed: {revision}")
            
            self.logger.audit_event(
                "database_upgrade",
                f"migration#{revision}",
                result="success",
                backup_created=create_backup
            )
            
            return execution
            
        except Exception as e:
            execution.status = MigrationStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            
            self.logger.error(f"Database upgrade failed: {str(e)}")
            
            # Attempt rollback if backup available
            if execution.rollback_available and execution.backup_path:
                self.logger.info("Attempting automatic rollback...")
                try:
                    self._rollback_from_backup(execution.backup_path)
                    execution.status = MigrationStatus.ROLLED_BACK
                    self.logger.info("Automatic rollback completed")
                except Exception as rollback_error:
                    self.logger.error(f"Rollback also failed: {str(rollback_error)}")
            
            raise create_database_error("MIGRATION_UPGRADE_FAILED", str(e))
    
    def downgrade_database(
        self,
        revision: str,
        create_backup: bool = True
    ) -> MigrationExecution:
        """
        Downgrade database to specified revision
        
        Args:
            revision: Target revision
            create_backup: Whether to create backup before migration
            
        Returns:
            MigrationExecution: Execution record
        """
        
        execution_id = f"downgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        execution = MigrationExecution(
            execution_id=execution_id,
            revision_id=revision,
            operation="downgrade",
            status=MigrationStatus.PENDING,
            started_at=datetime.utcnow()
        )
        
        try:
            execution.status = MigrationStatus.RUNNING
            self.execution_history.append(execution)
            
            self.logger.info(f"Starting database downgrade to {revision}")
            
            # Create backup if requested
            if create_backup:
                execution.backup_path = self._create_pre_migration_backup()
                execution.rollback_available = True
            
            # Execute downgrade
            config = Config(str(self.alembic_config_path))
            command.downgrade(config, revision)
            
            # Mark as completed
            execution.status = MigrationStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            
            self.logger.info(f"Database downgrade completed: {revision}")
            
            self.logger.audit_event(
                "database_downgrade",
                f"migration#{revision}",
                result="success",
                backup_created=create_backup
            )
            
            return execution
            
        except Exception as e:
            execution.status = MigrationStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            
            self.logger.error(f"Database downgrade failed: {str(e)}")
            
            raise create_database_error("MIGRATION_DOWNGRADE_FAILED", str(e))
    
    def _create_pre_migration_backup(self) -> str:
        """Create database backup before migration"""
        
        try:
            # Use backup manager if available
            try:
                from data_protection.backup_manager import get_backup_manager
                backup_manager = get_backup_manager()
                
                backup_name = f"pre_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_info = backup_manager.create_backup(
                    backup_type="FULL",
                    custom_name=backup_name
                )
                
                return backup_info.file_path
                
            except:
                # Fallback to simple pg_dump
                return self._simple_backup()
                
        except Exception as e:
            self.logger.warning(f"Failed to create pre-migration backup: {str(e)}")
            return None
    
    def _simple_backup(self) -> str:
        """Create simple database backup using pg_dump"""
        
        # Extract database info from URL
        from urllib.parse import urlparse
        parsed = urlparse(self.database_url)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"migration_backup_{timestamp}.sql"
        
        cmd = [
            "pg_dump",
            "-h", parsed.hostname,
            "-p", str(parsed.port or 5432),
            "-U", parsed.username,
            "-d", parsed.path[1:],  # Remove leading /
            "-f", backup_file,
            "--verbose"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise DatabaseError(
                message_es="Error al crear respaldo antes de la migración.",
                message_en="Failed to create pre-migration backup",
                technical_details=result.stderr
            )
        
        return os.path.abspath(backup_file)
    
    def _rollback_from_backup(self, backup_path: str):
        """Rollback database from backup"""
        
        # This is a destructive operation and should be used carefully
        from urllib.parse import urlparse
        parsed = urlparse(self.database_url)
        
        cmd = [
            "psql",
            "-h", parsed.hostname,
            "-p", str(parsed.port or 5432),
            "-U", parsed.username,
            "-d", parsed.path[1:],
            "-f", backup_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise DatabaseError(
                message_es="Error al restaurar desde el respaldo.",
                message_en="Failed to rollback from backup",
                technical_details=result.stderr
            )
    
    def validate_migration(self, revision: str) -> Dict[str, Any]:
        """
        Validate a migration without applying it
        
        Args:
            revision: Migration revision to validate
            
        Returns:
            Dict with validation results
        """
        
        try:
            config = Config(str(self.alembic_config_path))
            script = ScriptDirectory.from_config(config)
            
            # Get migration script
            migration_script = script.get_revision(revision)
            
            if not migration_script:
                return {
                    "valid": False,
                    "error": f"Migration {revision} not found"
                }
            
            # Basic validation
            validation_results = {
                "valid": True,
                "revision": revision,
                "description": migration_script.doc,
                "up_revision": migration_script.up_revision,
                "down_revision": migration_script.down_revision,
                "warnings": [],
                "recommendations": []
            }
            
            # Check for potential issues
            script_path = script.get_version_path(revision)
            if script_path and os.path.exists(script_path):
                with open(script_path, 'r') as f:
                    script_content = f.read()
                
                # Look for potentially dangerous operations
                dangerous_ops = [
                    "drop_table", "drop_column", "alter_column",
                    "execute('DROP", "execute('DELETE", "execute('TRUNCATE"
                ]
                
                for op in dangerous_ops:
                    if op in script_content:
                        validation_results["warnings"].append(
                            f"Potentially destructive operation detected: {op}"
                        )
                
                # Recommendations
                if "create_index" in script_content:
                    validation_results["recommendations"].append(
                        "Consider creating indexes with CONCURRENTLY option for production"
                    )
            
            return validation_results
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get comprehensive migration status"""
        
        try:
            current_revision = self.get_current_revision()
            migrations = self.get_migration_history()
            
            pending_migrations = [m for m in migrations if not m.is_applied]
            applied_migrations = [m for m in migrations if m.is_applied]
            
            status = {
                "current_revision": current_revision,
                "total_migrations": len(migrations),
                "applied_migrations": len(applied_migrations),
                "pending_migrations": len(pending_migrations),
                "migration_history": [
                    {
                        "revision": m.revision_id,
                        "description": m.description,
                        "applied": m.is_applied
                    }
                    for m in migrations
                ],
                "recent_executions": [
                    {
                        "execution_id": e.execution_id,
                        "operation": e.operation,
                        "revision": e.revision_id,
                        "status": e.status,
                        "started_at": e.started_at.isoformat(),
                        "completed_at": e.completed_at.isoformat() if e.completed_at else None
                    }
                    for e in self.execution_history[-10:]  # Last 10 executions
                ]
            }
            
            return status
            
        except Exception as e:
            return {"error": str(e)}


# === GLOBAL INSTANCE ===
migration_manager: Optional[DatabaseMigrationManager] = None


def initialize_migration_system(
    database_url: str,
    alembic_config_path: str = "alembic.ini",
    migrations_dir: str = "alembic"
) -> DatabaseMigrationManager:
    """Initialize the database migration system"""
    global migration_manager
    
    migration_manager = DatabaseMigrationManager(
        database_url, alembic_config_path, migrations_dir
    )
    logger = get_logger()
    logger.info("Database migration system initialized")
    
    return migration_manager


def get_migration_manager() -> DatabaseMigrationManager:
    """Get the global migration manager instance"""
    global migration_manager
    
    if migration_manager is None:
        raise RuntimeError("Migration system not initialized")
    
    return migration_manager