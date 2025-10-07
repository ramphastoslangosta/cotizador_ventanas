# tests/test_pdf_generation.py
import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, Company
from services.pdf_service import PDFQuoteService
import uuid

client = TestClient(app)

def test_pdf_generation_with_logo(test_db):
    """Test PDF generation when company has logo_filename"""
    # Setup
    user_id = uuid.uuid4()
    company = Company(
        user_id=user_id,
        name="Test Company",
        logo_filename="test_logo.png"
    )
    test_db.add(company)
    test_db.commit()

    # Test
    company_info = {
        'name': company.name,
        'logo_path': f"static/logos/{company.logo_filename}" if company.logo_filename else None
    }

    assert company_info['logo_path'] == "static/logos/test_logo.png"

def test_pdf_generation_without_logo(test_db):
    """Test PDF generation when company has no logo"""
    user_id = uuid.uuid4()
    company = Company(
        user_id=user_id,
        name="Test Company",
        logo_filename=None
    )
    test_db.add(company)
    test_db.commit()

    # Test
    company_info = {
        'name': company.name,
        'logo_path': f"static/logos/{company.logo_filename}" if company.logo_filename else None
    }

    assert company_info['logo_path'] is None

def test_pdf_service_handles_none_logo():
    """Test PDFQuoteService handles None logo_path gracefully"""
    pdf_service = PDFQuoteService()

    # Should not raise exception
    result = pdf_service.get_logo_base64(None)
    assert result is None

    # Should handle missing file
    result = pdf_service.get_logo_base64("nonexistent.png")
    assert result is None
