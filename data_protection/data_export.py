# data_protection/data_export.py
"""
Data Export System for Window Quotation System
Milestone 1.3: Data Protection

Features:
- User data export in multiple formats (JSON, CSV, PDF)
- GDPR-compliant data export
- Selective data export (user chooses what to export)
- Secure download links with expiration
- Audit trail for export operations
- Batch export capabilities
"""

import csv
import json
import zipfile
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import inspect
from io import StringIO, BytesIO

from error_handling.logging_config import get_logger
from error_handling.error_manager import create_database_error, create_business_error


class ExportFormat(str, Enum):
    """Supported export formats"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    ZIP = "zip"  # Multiple formats in one archive


class ExportStatus(str, Enum):
    """Export operation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class ExportRequest:
    """Data export request information"""
    export_id: str
    user_id: str
    request_timestamp: datetime
    export_format: ExportFormat
    data_types: List[str]  # Types of data to export (quotes, materials, etc.)
    status: ExportStatus
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DataExportManager:
    """
    Manage user data exports with GDPR compliance
    """
    
    def __init__(self, export_dir: str = "exports", link_expiry_hours: int = 24):
        """
        Initialize data export manager
        
        Args:
            export_dir: Directory to store export files
            link_expiry_hours: Hours until download link expires
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True, parents=True)
        self.link_expiry_hours = link_expiry_hours
        self.logger = get_logger()
        
        # In-memory export tracking (in production, use database)
        self.export_requests: Dict[str, ExportRequest] = {}
    
    def request_data_export(
        self,
        user_id: str,
        data_types: List[str],
        export_format: ExportFormat = ExportFormat.JSON,
        include_deleted: bool = False
    ) -> ExportRequest:
        """
        Create a new data export request
        
        Args:
            user_id: ID of user requesting export
            data_types: Types of data to export
            export_format: Format for export
            include_deleted: Include soft-deleted records
            
        Returns:
            ExportRequest object
        """
        
        export_id = str(uuid.uuid4())
        download_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=self.link_expiry_hours)
        
        export_request = ExportRequest(
            export_id=export_id,
            user_id=user_id,
            request_timestamp=datetime.utcnow(),
            export_format=export_format,
            data_types=data_types,
            status=ExportStatus.PENDING,
            download_token=download_token,
            expires_at=expires_at,
            metadata={
                "include_deleted": include_deleted,
                "user_agent": "web",  # Could be passed from request
                "ip_address": "unknown"  # Could be passed from request
            }
        )
        
        self.export_requests[export_id] = export_request
        
        self.logger.audit_event(
            "data_export_requested",
            f"export#{export_id}",
            user_id=user_id,
            result="success",
            data_types=",".join(data_types),
            format=export_format
        )
        
        self.logger.info(
            f"Data export requested: {export_id}",
            export_id=export_id,
            user_id=user_id,
            data_types=data_types,
            format=export_format
        )
        
        return export_request
    
    def process_export_request(
        self,
        session: Session,
        export_id: str
    ) -> ExportRequest:
        """
        Process a data export request
        
        Args:
            session: Database session
            export_id: ID of export request
            
        Returns:
            Updated ExportRequest object
        """
        
        if export_id not in self.export_requests:
            raise create_business_error("EXPORT_NOT_FOUND", f"Export ID: {export_id}")
        
        export_request = self.export_requests[export_id]
        
        if export_request.status != ExportStatus.PENDING:
            raise create_business_error("EXPORT_NOT_PENDING", 
                                      f"Export {export_id} status: {export_request.status}")
        
        try:
            export_request.status = ExportStatus.PROCESSING
            
            self.logger.info(f"Processing export request: {export_id}")
            
            # Collect user data based on requested types
            user_data = self._collect_user_data(session, export_request)
            
            # Generate export file
            file_path = self._generate_export_file(export_request, user_data)
            
            # Update export request
            export_request.file_path = str(file_path)
            export_request.file_size = file_path.stat().st_size
            export_request.status = ExportStatus.COMPLETED
            
            self.logger.audit_event(
                "data_export_completed",
                f"export#{export_id}",
                user_id=export_request.user_id,
                result="success",
                file_size=export_request.file_size
            )
            
            self.logger.info(
                f"Export completed: {export_id}",
                export_id=export_id,
                file_size=export_request.file_size,
                file_path=export_request.file_path
            )
            
            return export_request
            
        except Exception as e:
            export_request.status = ExportStatus.FAILED
            export_request.error_message = str(e)
            
            self.logger.error(f"Export failed: {export_id} - {str(e)}")
            
            self.logger.audit_event(
                "data_export_failed",
                f"export#{export_id}",
                user_id=export_request.user_id,
                result="failed",
                error=str(e)
            )
            
            raise
    
    def _collect_user_data(
        self,
        session: Session,
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """
        Collect user data based on export request
        
        Args:
            session: Database session
            export_request: Export request object
            
        Returns:
            Dictionary containing user data
        """
        
        user_data = {
            "export_info": {
                "export_id": export_request.export_id,
                "generated_at": datetime.utcnow().isoformat(),
                "user_id": export_request.user_id,
                "data_types": export_request.data_types,
                "format": export_request.export_format,
                "include_deleted": export_request.metadata.get("include_deleted", False)
            },
            "data": {}
        }
        
        # Import here to avoid circular imports
        from database import User, Quote, AppMaterial, AppProduct
        
        include_deleted = export_request.metadata.get("include_deleted", False)
        
        for data_type in export_request.data_types:
            try:
                if data_type == "profile":
                    # User profile data
                    user = session.query(User).filter(User.id == export_request.user_id).first()
                    if user:
                        user_data["data"]["profile"] = {
                            "id": user.id,
                            "email": user.email,
                            "full_name": user.full_name,
                            "created_at": user.created_at.isoformat() if user.created_at else None
                        }
                
                elif data_type == "quotes":
                    # User's quotes
                    query = session.query(Quote).filter(Quote.user_id == export_request.user_id)
                    
                    if not include_deleted and hasattr(Quote, 'is_deleted'):
                        query = query.filter(Quote.is_deleted == False)
                    
                    quotes = query.all()
                    user_data["data"]["quotes"] = []
                    
                    for quote in quotes:
                        quote_data = {
                            "id": quote.id,
                            "client_info": quote.client_info,
                            "quote_data": quote.quote_data,
                            "total_amount": float(quote.total_amount) if quote.total_amount else None,
                            "created_at": quote.created_at.isoformat() if quote.created_at else None,
                            "updated_at": quote.updated_at.isoformat() if quote.updated_at else None
                        }
                        
                        # Include soft delete info if applicable
                        if include_deleted and hasattr(quote, 'is_deleted'):
                            quote_data["is_deleted"] = quote.is_deleted
                            quote_data["deleted_at"] = quote.deleted_at.isoformat() if quote.deleted_at else None
                            quote_data["delete_reason"] = quote.delete_reason
                        
                        user_data["data"]["quotes"].append(quote_data)
                
                elif data_type == "materials" and export_request.user_id == "admin":
                    # Materials data (only for admin users)
                    query = session.query(AppMaterial)
                    
                    if not include_deleted and hasattr(AppMaterial, 'is_deleted'):
                        query = query.filter(AppMaterial.is_deleted == False)
                    
                    materials = query.all()
                    user_data["data"]["materials"] = []
                    
                    for material in materials:
                        material_data = {
                            "id": material.id,
                            "name": material.name,
                            "code": material.code,
                            "unit": material.unit,
                            "cost_per_unit": float(material.cost_per_unit),
                            "category": material.category
                        }
                        
                        if include_deleted and hasattr(material, 'is_deleted'):
                            material_data["is_deleted"] = material.is_deleted
                            material_data["deleted_at"] = material.deleted_at.isoformat() if material.deleted_at else None
                        
                        user_data["data"]["materials"].append(material_data)
                
                elif data_type == "products" and export_request.user_id == "admin":
                    # Products data (only for admin users)
                    query = session.query(AppProduct)
                    
                    if not include_deleted and hasattr(AppProduct, 'is_deleted'):
                        query = query.filter(AppProduct.is_deleted == False)
                    
                    products = query.all()
                    user_data["data"]["products"] = []
                    
                    for product in products:
                        product_data = {
                            "id": product.id,
                            "name": product.name,
                            "window_type": product.window_type,
                            "aluminum_line": product.aluminum_line,
                            "bom": product.bom
                        }
                        
                        if include_deleted and hasattr(product, 'is_deleted'):
                            product_data["is_deleted"] = product.is_deleted
                            product_data["deleted_at"] = product.deleted_at.isoformat() if product.deleted_at else None
                        
                        user_data["data"]["products"].append(product_data)
                
            except Exception as e:
                self.logger.warning(f"Failed to collect {data_type} data for user {export_request.user_id}: {str(e)}")
                user_data["data"][data_type] = {"error": f"Failed to collect data: {str(e)}"}
        
        return user_data
    
    def _generate_export_file(
        self,
        export_request: ExportRequest,
        user_data: Dict[str, Any]
    ) -> Path:
        """
        Generate export file in requested format
        
        Args:
            export_request: Export request object
            user_data: User data to export
            
        Returns:
            Path to generated file
        """
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_filename = f"export_{export_request.user_id}_{timestamp}"
        
        if export_request.export_format == ExportFormat.JSON:
            return self._generate_json_export(export_request, user_data, base_filename)
        
        elif export_request.export_format == ExportFormat.CSV:
            return self._generate_csv_export(export_request, user_data, base_filename)
        
        elif export_request.export_format == ExportFormat.ZIP:
            return self._generate_zip_export(export_request, user_data, base_filename)
        
        else:
            raise create_business_error("UNSUPPORTED_FORMAT", 
                                      f"Format: {export_request.export_format}")
    
    def _generate_json_export(
        self,
        export_request: ExportRequest,
        user_data: Dict[str, Any],
        base_filename: str
    ) -> Path:
        """Generate JSON export file"""
        
        file_path = self.export_dir / f"{base_filename}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=2, ensure_ascii=False, default=str)
        
        return file_path
    
    def _generate_csv_export(
        self,
        export_request: ExportRequest,
        user_data: Dict[str, Any],
        base_filename: str
    ) -> Path:
        """Generate CSV export files (one per data type)"""
        
        zip_path = self.export_dir / f"{base_filename}_csv.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add export info as JSON
            info_json = json.dumps(user_data["export_info"], indent=2, default=str)
            zipf.writestr("export_info.json", info_json)
            
            # Convert each data type to CSV
            for data_type, data in user_data["data"].items():
                if isinstance(data, list) and data:
                    csv_content = self._convert_to_csv(data)
                    zipf.writestr(f"{data_type}.csv", csv_content)
                elif isinstance(data, dict):
                    # Convert single object to CSV
                    csv_content = self._convert_to_csv([data])
                    zipf.writestr(f"{data_type}.csv", csv_content)
        
        return zip_path
    
    def _generate_zip_export(
        self,
        export_request: ExportRequest,
        user_data: Dict[str, Any],
        base_filename: str
    ) -> Path:
        """Generate ZIP export with multiple formats"""
        
        zip_path = self.export_dir / f"{base_filename}_complete.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON version
            json_content = json.dumps(user_data, indent=2, ensure_ascii=False, default=str)
            zipf.writestr("complete_export.json", json_content)
            
            # Add CSV versions
            for data_type, data in user_data["data"].items():
                if isinstance(data, list) and data:
                    csv_content = self._convert_to_csv(data)
                    zipf.writestr(f"csv/{data_type}.csv", csv_content)
            
            # Add metadata
            metadata = {
                "export_id": export_request.export_id,
                "generated_at": datetime.utcnow().isoformat(),
                "formats_included": ["json", "csv"],
                "data_types": export_request.data_types
            }
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        return zip_path
    
    def _convert_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """Convert list of dictionaries to CSV format"""
        
        if not data:
            return ""
        
        output = StringIO()
        
        # Get all possible fieldnames from all records
        fieldnames = set()
        for record in data:
            fieldnames.update(record.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in data:
            # Convert complex objects to strings
            clean_record = {}
            for key, value in record.items():
                if isinstance(value, (dict, list)):
                    clean_record[key] = json.dumps(value, default=str)
                else:
                    clean_record[key] = value
            
            writer.writerow(clean_record)
        
        return output.getvalue()
    
    def get_download_info(self, download_token: str) -> Optional[ExportRequest]:
        """
        Get export information by download token
        
        Args:
            download_token: Secure download token
            
        Returns:
            ExportRequest if valid, None otherwise
        """
        
        for export_request in self.export_requests.values():
            if export_request.download_token == download_token:
                # Check if not expired
                if export_request.expires_at and datetime.utcnow() > export_request.expires_at:
                    export_request.status = ExportStatus.EXPIRED
                    return None
                
                return export_request
        
        return None
    
    def get_export_file(self, download_token: str) -> Optional[Path]:
        """
        Get export file path by download token
        
        Args:
            download_token: Secure download token
            
        Returns:
            Path to export file if valid, None otherwise
        """
        
        export_request = self.get_download_info(download_token)
        
        if not export_request or export_request.status != ExportStatus.COMPLETED:
            return None
        
        file_path = Path(export_request.file_path)
        
        if not file_path.exists():
            export_request.status = ExportStatus.FAILED
            export_request.error_message = "Export file not found"
            return None
        
        # Log download
        self.logger.audit_event(
            "data_export_downloaded",
            f"export#{export_request.export_id}",
            user_id=export_request.user_id,
            result="success"
        )
        
        return file_path
    
    def cleanup_expired_exports(self) -> Dict[str, int]:
        """
        Clean up expired export files and requests
        
        Returns:
            Dictionary with cleanup statistics
        """
        
        cleaned_files = 0
        cleaned_requests = 0
        
        current_time = datetime.utcnow()
        expired_exports = []
        
        # Find expired exports
        for export_id, export_request in self.export_requests.items():
            if export_request.expires_at and current_time > export_request.expires_at:
                expired_exports.append(export_id)
        
        # Clean up expired exports
        for export_id in expired_exports:
            export_request = self.export_requests[export_id]
            
            # Remove file if exists
            if export_request.file_path:
                file_path = Path(export_request.file_path)
                if file_path.exists():
                    try:
                        file_path.unlink()
                        cleaned_files += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove export file {file_path}: {e}")
            
            # Remove request
            del self.export_requests[export_id]
            cleaned_requests += 1
        
        if cleaned_requests > 0:
            self.logger.info(f"Cleaned up {cleaned_requests} expired exports, {cleaned_files} files")
        
        return {
            "cleaned_requests": cleaned_requests,
            "cleaned_files": cleaned_files,
            "remaining_exports": len(self.export_requests)
        }
    
    def get_user_exports(self, user_id: str) -> List[ExportRequest]:
        """
        Get all export requests for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of export requests
        """
        
        user_exports = [
            export_request for export_request in self.export_requests.values()
            if export_request.user_id == user_id
        ]
        
        # Sort by request timestamp (newest first)
        user_exports.sort(key=lambda x: x.request_timestamp, reverse=True)
        
        return user_exports


# === GLOBAL INSTANCE ===
data_export_manager: Optional[DataExportManager] = None


def initialize_data_export_system(
    export_dir: str = "exports",
    link_expiry_hours: int = 24
) -> DataExportManager:
    """Initialize the data export system"""
    global data_export_manager
    
    data_export_manager = DataExportManager(export_dir, link_expiry_hours)
    logger = get_logger()
    logger.info(f"Data export system initialized with {link_expiry_hours}h link expiry")
    
    return data_export_manager


def get_data_export_manager() -> DataExportManager:
    """Get the global data export manager instance"""
    global data_export_manager
    
    if data_export_manager is None:
        raise RuntimeError("Data export system not initialized")
    
    return data_export_manager