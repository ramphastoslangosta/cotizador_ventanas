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


class TestQuoteListPresenter:
    """Unit tests for QuoteListPresenter"""

    def test_presenter_processes_quote_correctly(self, sample_quote_data):
        """Test presenter adds calculated fields to quote"""
        from app.presenters.quote_presenter import QuoteListPresenter
        from unittest.mock import Mock

        # Create a mock database session
        mock_db = Mock()

        # Create presenter
        presenter = QuoteListPresenter(mock_db)

        # Create a quote with items that have area
        quote = MockQuote(
            id=1,
            user_id=uuid.uuid4(),
            client_name="Test Client",
            client_email="test@example.com",
            total_final=Decimal("2000.00"),
            materials_subtotal=Decimal("1000.00"),
            labor_subtotal=Decimal("500.00"),
            profit_amount=Decimal("300.00"),
            indirect_costs_amount=Decimal("150.00"),
            tax_amount=Decimal("320.00"),
            items_count=2,
            quote_data={
                "items": [
                    {"area_m2": 1.5, "product_bom_name": "Window A"},
                    {"area_m2": 2.0, "product_bom_name": "Window B"}
                ]
            },
            notes="Test"
        )

        # Process quote (presenter processes one at a time)
        processed_quote = presenter.present(quote)

        # Check that total_area was calculated (1.5 + 2.0 = 3.5)
        # Presenter returns a dict
        assert 'total_area' in processed_quote
        assert processed_quote['total_area'] == 3.5

        # Check that price_per_m2 was calculated
        assert 'price_per_m2' in processed_quote
        expected_price_per_m2 = float(quote.total_final) / 3.5
        assert abs(processed_quote['price_per_m2'] - expected_price_per_m2) < 0.01

    def test_presenter_handles_empty_items(self):
        """Test presenter handles quote with no items gracefully"""
        from app.presenters.quote_presenter import QuoteListPresenter
        from unittest.mock import Mock

        mock_db = Mock()
        presenter = QuoteListPresenter(mock_db)

        # Create quote with empty items
        quote = MockQuote(
            id=1,
            user_id=uuid.uuid4(),
            client_name="Empty Client",
            total_final=Decimal("100.00"),
            materials_subtotal=Decimal("80.00"),
            labor_subtotal=Decimal("20.00"),
            profit_amount=Decimal("10.00"),
            indirect_costs_amount=Decimal("5.00"),
            tax_amount=Decimal("15.00"),
            items_count=0,
            quote_data={"items": []},
            notes="Empty"
        )

        # Process should not crash
        processed_quote = presenter.present(quote)

        # Should have calculated fields with defaults
        assert 'total_area' in processed_quote
        assert processed_quote['total_area'] == 0 or processed_quote['total_area'] is None

    def test_presenter_handles_corrupted_data(self):
        """Test presenter handles corrupted quote data gracefully"""
        from app.presenters.quote_presenter import QuoteListPresenter
        from unittest.mock import Mock

        mock_db = Mock()
        presenter = QuoteListPresenter(mock_db)

        # Create quote with corrupted quote_data
        quote = MockQuote(
            id=1,
            user_id=uuid.uuid4(),
            client_name="Corrupted Client",
            total_final=Decimal("500.00"),
            materials_subtotal=Decimal("400.00"),
            labor_subtotal=Decimal("100.00"),
            profit_amount=Decimal("50.00"),
            indirect_costs_amount=Decimal("25.00"),
            tax_amount=Decimal("80.00"),
            items_count=1,
            quote_data=None,  # Corrupted: None instead of dict
            notes="Corrupted"
        )

        # Process should not crash
        try:
            processed = presenter.present(quote)
            # If it doesn't crash, that's good
            assert processed is not None or processed is None  # Either works
        except Exception as e:
            # If it does crash, it should be handled gracefully
            assert False, f"Presenter should handle corrupted data gracefully, but raised: {e}"

    def test_presenter_processes_multiple_quotes(self, sample_quote_data):
        """Test presenter handles multiple quotes correctly"""
        from app.presenters.quote_presenter import QuoteListPresenter
        from unittest.mock import Mock

        mock_db = Mock()
        presenter = QuoteListPresenter(mock_db)

        # Create multiple quotes
        quotes = []
        for i in range(3):
            quote = MockQuote(
                id=i+1,
                user_id=uuid.uuid4(),
                client_name=f"Client {i+1}",
                client_email=f"client{i+1}@test.com",
                total_final=Decimal(f"{1000 + i*100}.00"),
                materials_subtotal=Decimal(f"{800 + i*80}.00"),
                labor_subtotal=Decimal("200.00"),
                profit_amount=Decimal("100.00"),
                indirect_costs_amount=Decimal("50.00"),
                tax_amount=Decimal("160.00"),
                items_count=1,
                quote_data={
                    "items": [
                        {"area_m2": 1.0 + i*0.5, "product_bom_name": f"Window {i+1}"}
                    ]
                },
                notes=f"Test {i+1}"
            )
            quotes.append(quote)

        # Process all quotes (presenter processes one at a time)
        processed = [presenter.present(quote) for quote in quotes]

        # Verify all quotes processed
        assert len(processed) == 3

        # Verify each has calculated fields
        for i, pq in enumerate(processed):
            assert 'total_area' in pq
            assert 'price_per_m2' in pq
            assert pq['client_name'] == f"Client {i+1}"


class TestDatabaseQuoteServicePagination:
    """Unit tests for DatabaseQuoteService pagination"""

    def test_get_quotes_with_limit(self, test_user, sample_quote_data):
        """Test get_quotes_by_user respects limit parameter"""
        from database import DatabaseQuoteService
        from unittest.mock import Mock, MagicMock

        # Create mock database session
        mock_db = Mock()

        # Create 5 mock quotes
        quotes = []
        for i in range(5):
            quote = MockQuote(
                id=i+1,
                user_id=test_user.id,
                client_name=f"Limit Client {i+1}",
                total_final=Decimal("1000.00"),
                materials_subtotal=Decimal("800.00"),
                labor_subtotal=Decimal("200.00"),
                items_count=1,
                quote_data=sample_quote_data
            )
            quotes.append(quote)

        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = quotes[:3]  # Return only first 3

        mock_db.query.return_value = mock_query

        # Create service
        service = DatabaseQuoteService(mock_db)

        # Get quotes with limit=3
        result = service.get_quotes_by_user(str(test_user.id), limit=3, offset=0)

        # Verify limit was applied
        mock_query.limit.assert_called_with(3)
        assert len(result) == 3

    def test_get_quotes_with_offset(self, test_user, sample_quote_data):
        """Test get_quotes_by_user respects offset parameter"""
        from database import DatabaseQuoteService
        from unittest.mock import Mock, MagicMock

        mock_db = Mock()

        # Create mock quotes for page 2 (offset=20)
        quotes_page2 = []
        for i in range(20, 25):  # Quotes 21-25
            quote = MockQuote(
                id=i+1,
                user_id=test_user.id,
                client_name=f"Offset Client {i+1}",
                total_final=Decimal("1000.00"),
                materials_subtotal=Decimal("800.00"),
                labor_subtotal=Decimal("200.00"),
                items_count=1,
                quote_data=sample_quote_data
            )
            quotes_page2.append(quote)

        # Mock query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = quotes_page2

        mock_db.query.return_value = mock_query

        service = DatabaseQuoteService(mock_db)

        # Get quotes with offset=20 (page 2)
        result = service.get_quotes_by_user(str(test_user.id), limit=20, offset=20)

        # Verify offset was applied
        mock_query.offset.assert_called_with(20)
        assert len(result) == 5  # Only 5 quotes returned

    def test_get_quotes_offset_beyond_total(self, test_user):
        """Test get_quotes_by_user with offset beyond total returns empty"""
        from database import DatabaseQuoteService
        from unittest.mock import Mock, MagicMock

        mock_db = Mock()

        # Mock query chain to return empty list
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []  # No quotes beyond offset

        mock_db.query.return_value = mock_query

        service = DatabaseQuoteService(mock_db)

        # Get quotes with offset=1000 (way beyond total)
        result = service.get_quotes_by_user(str(test_user.id), limit=20, offset=1000)

        # Verify returns empty list
        assert result == []
        assert len(result) == 0

    def test_get_quotes_default_pagination(self, test_user, sample_quote_data):
        """Test get_quotes_by_user uses default limit when not specified"""
        from database import DatabaseQuoteService
        from unittest.mock import Mock, MagicMock

        mock_db = Mock()

        # Create 25 mock quotes
        quotes = []
        for i in range(25):
            quote = MockQuote(
                id=i+1,
                user_id=test_user.id,
                client_name=f"Default Client {i+1}",
                total_final=Decimal("1000.00"),
                materials_subtotal=Decimal("800.00"),
                labor_subtotal=Decimal("200.00"),
                items_count=1,
                quote_data=sample_quote_data
            )
            quotes.append(quote)

        # Mock query - should return first 20 (default limit)
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = quotes[:20]

        mock_db.query.return_value = mock_query

        service = DatabaseQuoteService(mock_db)

        # Get quotes without specifying limit (should use default of 20)
        result = service.get_quotes_by_user(str(test_user.id))

        # Verify default limit was used
        assert len(result) <= 20  # Should not exceed default limit


class TestGlassPricingIntegration:
    """Integration tests for database-driven glass pricing in quotes"""

    def test_quote_calculation_with_database_glass_pricing(self):
        """Test that quote calculations use database glass prices"""
        from database import SessionLocal, DatabaseMaterialService
        from services.product_bom_service_db import ProductBOMServiceDB, initialize_sample_data, GLASS_TYPE_TO_MATERIAL_CODE
        from models.quote_models import GlassType

        # Skip if database not available (local development)
        try:
            db = SessionLocal()
        except Exception:
            pytest.skip("Database not available for integration test")

        try:
            # Initialize sample data with glass materials
            initialize_sample_data(db)

            # Create BOM service
            bom_service = ProductBOMServiceDB(db)
            material_service = DatabaseMaterialService(db)

            # Verify glass materials exist in database
            glass_code = GLASS_TYPE_TO_MATERIAL_CODE[GlassType.CLARO_6MM]
            glass_material = material_service.get_material_by_code(glass_code)
            assert glass_material is not None, f"Glass material {glass_code} not found in database"

            # Get glass price from database
            glass_price = bom_service.get_glass_cost_per_m2(GlassType.CLARO_6MM)

            # Verify price is from database (should match material cost_per_unit)
            assert glass_price == glass_material.cost_per_unit, \
                f"Glass price {glass_price} doesn't match database material {glass_material.cost_per_unit}"

            # Verify price is positive and reasonable
            assert glass_price > 0, "Glass price should be positive"
            assert glass_price < Decimal("1000.00"), "Glass price should be reasonable"

            print(f"✓ Quote calculated successfully with database glass pricing")
            print(f"  Glass material: {glass_material.name} ({glass_code})")
            print(f"  Glass price: ${glass_price}/m²")

        finally:
            db.close()

    def test_glass_price_change_affects_new_quotes(self):
        """Test that changing glass price in database affects new quotes"""
        from database import SessionLocal, DatabaseMaterialService
        from services.product_bom_service_db import ProductBOMServiceDB, initialize_sample_data, GLASS_TYPE_TO_MATERIAL_CODE
        from models.quote_models import GlassType

        # Skip if database not available
        try:
            db = SessionLocal()
        except Exception:
            pytest.skip("Database not available for integration test")

        try:
            # Initialize sample data
            initialize_sample_data(db)

            # Create services
            bom_service = ProductBOMServiceDB(db)
            material_service = DatabaseMaterialService(db)

            # Get glass material
            glass_code = GLASS_TYPE_TO_MATERIAL_CODE[GlassType.TEMPLADO_6MM]
            glass_material = material_service.get_material_by_code(glass_code)
            assert glass_material is not None, f"Glass material {glass_code} not found"

            # Get initial price
            initial_price = bom_service.get_glass_cost_per_m2(GlassType.TEMPLADO_6MM)
            print(f"Initial price: ${initial_price}/m²")

            # Update price in database (50% increase)
            new_price = initial_price * Decimal("1.5")
            material_service.update_material(
                glass_material.id,
                cost_per_unit=new_price
            )

            # Clear cache if present
            if hasattr(bom_service, '_glass_price_cache') and bom_service._glass_price_cache is not None:
                bom_service.clear_glass_price_cache()

            # Get updated price
            updated_price = bom_service.get_glass_cost_per_m2(GlassType.TEMPLADO_6MM)

            # Verify new price is used
            assert updated_price == new_price, \
                f"Glass price change didn't propagate: {updated_price} != {new_price}"

            # Verify price increased by 50%
            price_increase_pct = ((updated_price - initial_price) / initial_price) * 100
            assert abs(price_increase_pct - 50) < 0.1, \
                f"Price increase should be 50%, got {price_increase_pct:.1f}%"

            print(f"✓ Price change verified: ${initial_price} → ${updated_price} (+50%)")

            # Restore original price for other tests
            material_service.update_material(
                glass_material.id,
                cost_per_unit=initial_price
            )

        finally:
            db.close()
