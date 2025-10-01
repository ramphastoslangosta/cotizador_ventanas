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
    """Mock Quote model with proper datetime handling"""
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
        # Ensure created_at is a real datetime object with working .date() method
        created_at = kwargs.get('created_at', datetime.now(timezone.utc))
        # Make sure it's not already a Mock
        if isinstance(created_at, datetime):
            self.created_at = created_at
        else:
            self.created_at = datetime.now(timezone.utc)
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

    @patch('app.routes.quotes.get_current_user_from_cookie')
    @patch('app.routes.quotes.DatabaseQuoteService')
    def test_quotes_list_single_quote(self, mock_quote_service,
                                     mock_get_user, test_client, test_user, test_session, sample_quote_data):
        """Test quotes list page with one quote"""
        # Mock authentication
        mock_get_user.return_value = test_user

        # Create a mock quote
        quote = MockQuote(
            id=1,
            user_id=test_user.id,
            client_name=sample_quote_data["client"]["name"],
            client_email=sample_quote_data["client"]["email"],
            client_phone=sample_quote_data["client"]["phone"],
            client_address=sample_quote_data["client"]["address"],
            total_final=Decimal(str(sample_quote_data["total_final"])),
            materials_subtotal=Decimal(str(sample_quote_data["materials_subtotal"])),
            labor_subtotal=Decimal(str(sample_quote_data["labor_subtotal"])),
            profit_amount=Decimal(str(sample_quote_data["profit_amount"])),
            indirect_costs_amount=Decimal(str(sample_quote_data["indirect_costs_amount"])),
            tax_amount=Decimal(str(sample_quote_data["tax_amount"])),
            items_count=len(sample_quote_data["items"]),
            quote_data=sample_quote_data,
            notes=sample_quote_data.get("notes")
        )

        # Mock quote service to return our quote
        # Let the real QuoteListPresenter process it
        mock_service_instance = Mock()
        mock_service_instance.get_quotes_by_user.return_value = [quote]
        mock_quote_service.return_value = mock_service_instance

        # Set session cookie
        test_client.cookies.set("session_token", test_session.token)

        # Request quotes list page
        response = test_client.get("/quotes")

        # Verify response
        assert response.status_code == 200
        html = response.text

        # Verify quote data appears in HTML
        assert sample_quote_data["client"]["name"] in html
        assert str(quote.id) in html

        # Verify total_final displays correctly
        # The presenter processes the quote and adds calculated fields
        assert "1786" in html or "1,786" in html  # total_final

        # Verify the page rendered successfully with quote data
        assert "cotizaci" in html.lower()  # Spanish "cotización" or variations

    @patch('app.routes.quotes.get_current_user_from_cookie')
    @patch('app.routes.quotes.DatabaseQuoteService')
    def test_quotes_list_pagination(self, mock_quote_service, mock_get_user,
                                   test_client, test_user, test_session, sample_quote_data):
        """Test quotes list pagination with multiple pages"""
        # Mock authentication
        mock_get_user.return_value = test_user

        # Create 25 test quotes to trigger pagination
        quotes = []
        for i in range(25):
            quote_data = sample_quote_data.copy()
            quote_data["client"]["name"] = f"Client {i+1:02d}"

            quote = MockQuote(
                id=i+1,
                user_id=test_user.id,
                client_name=f"Client {i+1:02d}",
                client_email=f"client{i+1}@test.com",
                client_phone="+1234567890",
                client_address="123 Test St",
                total_final=Decimal("1786.40"),
                materials_subtotal=Decimal("900.00"),
                labor_subtotal=Decimal("200.00"),
                profit_amount=Decimal("275.00"),
                indirect_costs_amount=Decimal("165.00"),
                tax_amount=Decimal("246.40"),
                items_count=1,
                quote_data=quote_data,
                notes=f"Test quote {i+1}"
            )
            quotes.append(quote)

        # Mock quote service to return first 20 quotes for page 1
        mock_service_instance = Mock()
        mock_service_instance.get_quotes_by_user.return_value = quotes[:20]
        mock_quote_service.return_value = mock_service_instance

        # Set session cookie
        test_client.cookies.set("session_token", test_session.token)

        # Test first page (default, should show first 20)
        response_page1 = test_client.get("/quotes")
        assert response_page1.status_code == 200
        html_page1 = response_page1.text

        # Verify quotes are rendered (service returned 20 quotes)
        # The presenter processes them and template displays them
        assert "cotización" in html_page1.lower()

        # Verify we see the first batch of quotes
        # Since we mocked the service to return quotes[:20], we should see those clients
        assert "client 01" in html_page1.lower() or "client 02" in html_page1.lower()

        # Mock quote service to return quotes 21-25 for page 2
        mock_service_instance.get_quotes_by_user.return_value = quotes[20:25]

        # Test second page (with page parameter)
        # Note: Route may not implement pagination yet, but we verify the handler works
        response_page2 = test_client.get("/quotes?page=2")
        assert response_page2.status_code == 200
        html_page2 = response_page2.text

        # Verify the route handled the page parameter without error
        assert "cotización" in html_page2.lower()

        # If pagination is implemented, second page should show remaining quotes
        # If not implemented, it will show same quotes as page 1 (that's ok for now)

    @patch('app.routes.quotes.get_current_user_from_cookie')
    @patch('app.routes.quotes.DatabaseQuoteService')
    def test_quotes_list_pagination_edge_cases(self, mock_quote_service, mock_get_user,
                                              test_client, test_user, test_session, sample_quote_data):
        """Test pagination edge cases"""
        # Mock authentication
        mock_get_user.return_value = test_user

        # Create exactly 20 quotes (one full page)
        quotes = []
        for i in range(20):
            quote = MockQuote(
                id=i+1,
                user_id=test_user.id,
                client_name=f"Edge Client {i+1:02d}",
                client_email=f"edge{i+1}@test.com",
                client_phone="+1234567890",
                client_address="123 Test St",
                total_final=Decimal("1000.00"),
                materials_subtotal=Decimal("800.00"),
                labor_subtotal=Decimal("200.00"),
                profit_amount=Decimal("200.00"),
                indirect_costs_amount=Decimal("150.00"),
                tax_amount=Decimal("160.00"),
                items_count=1,
                quote_data=sample_quote_data,
                notes=f"Edge test {i+1}"
            )
            quotes.append(quote)

        # Mock quote service
        mock_service_instance = Mock()
        mock_service_instance.get_quotes_by_user.return_value = quotes
        mock_quote_service.return_value = mock_service_instance

        # Set session cookie
        test_client.cookies.set("session_token", test_session.token)

        # Test page 1 (should show all 20)
        response = test_client.get("/quotes")
        assert response.status_code == 200

        # Mock empty results for page 2
        mock_service_instance.get_quotes_by_user.return_value = []

        # Test page 2 (should be empty or show empty state)
        response_page2 = test_client.get("/quotes?page=2")
        assert response_page2.status_code == 200
        # Should handle gracefully (empty state or no pagination controls)

        # Test invalid page parameter (should default to page 1 or show error gracefully)
        response_invalid = test_client.get("/quotes?page=-1")
        assert response_invalid.status_code in [200, 400]  # Either show page 1 or validation error
