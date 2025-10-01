"""Integration tests for quote routes

HOTFIX-20251001-002: Prevent template rendering and router compatibility bugs
Tests the complete flow: Route → Presenter → Template → Response
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import uuid


# Import only what we need from main to avoid database import issues
# Database models will be mocked
class MockQuote:
    """Mock Quote model"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.user_id = kwargs.get('user_id', uuid.uuid4())
        self.client_name = kwargs.get('client_name', 'Test Client')
        self.client_email = kwargs.get('client_email', 'test@example.com')
        self.client_phone = kwargs.get('client_phone', '+1234567890')
        self.client_address = kwargs.get('client_address', '123 Test St')
        self.total_final = kwargs.get('total_final', Decimal('1786.40'))
        self.materials_subtotal = kwargs.get('materials_subtotal', Decimal('900.00'))
        self.labor_subtotal = kwargs.get('labor_subtotal', Decimal('200.00'))
        self.profit_amount = kwargs.get('profit_amount', Decimal('275.00'))
        self.indirect_costs_amount = kwargs.get('indirect_costs_amount', Decimal('165.00'))
        self.tax_amount = kwargs.get('tax_amount', Decimal('246.40'))
        self.items_count = kwargs.get('items_count', 1)
        self.quote_data = kwargs.get('quote_data', {})
        self.notes = kwargs.get('notes', 'Test quote')
        self.created_at = kwargs.get('created_at', datetime.now(timezone.utc))
        self.valid_until = kwargs.get('valid_until', datetime.now(timezone.utc) + timedelta(days=30))


class MockUser:
    """Mock User model"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid.uuid4())
        self.email = kwargs.get('email', 'test@example.com')
        self.full_name = kwargs.get('full_name', 'Test User')
        self.is_active = kwargs.get('is_active', True)


class MockSession:
    """Mock UserSession model"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid.uuid4())
        self.user_id = kwargs.get('user_id', uuid.uuid4())
        self.token = kwargs.get('token', 'test_token_123')
        self.expires_at = kwargs.get('expires_at', datetime.now(timezone.utc) + timedelta(hours=2))
        self.is_active = kwargs.get('is_active', True)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def test_user():
    """Create mock test user"""
    return MockUser(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        is_active=True
    )


@pytest.fixture
def test_session(test_user):
    """Create mock test session"""
    return MockSession(
        user_id=test_user.id,
        token="test_session_token_123",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        is_active=True
    )


@pytest.fixture
def test_client():
    """FastAPI test client with lazy import"""
    # Import here to avoid database.py import at module level
    from main import app as fastapi_app
    with TestClient(fastapi_app) as client:
        yield client


@pytest.fixture
def auth_cookie(test_session):
    """Authentication cookie for requests"""
    return {"session_token": test_session.token}


@pytest.fixture
def sample_quote_data():
    """Sample quote data for creating test quotes"""
    return {
        "client": {
            "name": "Test Client",
            "email": "client@test.com",
            "phone": "+1234567890",
            "address": "123 Test St"
        },
        "items": [
            {
                "product_bom_id": 1,
                "product_bom_name": "Ventana Corrediza",
                "window_type": "corrediza",
                "aluminum_line": "nacional_serie_3",
                "selected_glass_type": "claro_6mm",
                "width_cm": 150,
                "height_cm": 120,
                "quantity": 2,
                "area_m2": 1.8,
                "perimeter_m": 5.4,
                "total_profiles_cost": 450.00,
                "total_glass_cost": 280.00,
                "total_hardware_cost": 120.00,
                "total_consumables_cost": 50.00,
                "labor_cost": 200.00,
                "subtotal": 1100.00
            }
        ],
        "materials_subtotal": 900.00,
        "labor_subtotal": 200.00,
        "subtotal_before_overhead": 1100.00,
        "profit_amount": 275.00,
        "indirect_costs_amount": 165.00,
        "subtotal_with_overhead": 1540.00,
        "tax_amount": 246.40,
        "total_final": 1786.40,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "notes": "Test quote"
    }


# Mark as integration test
pytestmark = pytest.mark.integration


class TestQuotesListRoute:
    """Integration tests for GET /quotes route"""

    @patch('app.routes.quotes.get_current_user_from_cookie')
    @patch('app.routes.quotes.DatabaseQuoteService')
    def test_quotes_list_empty_state(self, mock_quote_service, mock_get_user, test_client, test_user, test_session):
        """Test quotes list page with no quotes"""
        # Mock authentication to return our test user
        mock_get_user.return_value = test_user

        # Mock quote service to return empty list
        mock_service_instance = Mock()
        mock_service_instance.get_quotes_by_user.return_value = []
        mock_quote_service.return_value = mock_service_instance

        # Set session cookie
        test_client.cookies.set("session_token", test_session.token)

        # Request quotes list page
        response = test_client.get("/quotes")

        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

        # Verify template rendered
        html = response.text
        assert "Cotizaciones" in html or "Quotes" in html or "cotizaciones" in html.lower()
        assert test_user.full_name in html  # User info displayed

        # Verify empty state message (adjust based on actual template)
        assert ("No hay cotizaciones" in html or
                "no quotes" in html.lower() or
                "no tienes cotizaciones" in html.lower() or
                "aún no has creado" in html.lower())

    @patch('app.routes.quotes.get_current_user_from_cookie')
    def test_quotes_list_without_authentication(self, mock_get_user, test_client):
        """Test quotes list redirects to login when not authenticated"""
        # Mock authentication to return None (not authenticated)
        mock_get_user.return_value = None

        response = test_client.get("/quotes", follow_redirects=False)

        # Should redirect to login
        assert response.status_code in [302, 303, 307]
        assert "/login" in response.headers.get("location", "")
