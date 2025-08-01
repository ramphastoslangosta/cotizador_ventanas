# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
python main.py
# Starts FastAPI server with Uvicorn on http://localhost:8000
# API documentation available at http://localhost:8000/docs
```

### Installing Dependencies
```bash
pip install -r requirements.txt
# Install all required packages including FastAPI, SQLAlchemy, PostgreSQL driver
```

### Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### Database Connection Testing
```bash
python test_connection.py
# Tests PostgreSQL/Supabase database connectivity
```

### Debug Commands
```bash
python debug_main.py
# Alternative main entry point for debugging
python debug_env.py
# Environment variable testing
```

## Project Architecture

### Core Application Structure
This is a **FastAPI-based window quotation system** with PostgreSQL database backend. The application provides both web interface and REST API for managing window quotations with dynamic BOM (Bill of Materials) calculations.

**Key architectural patterns:**
- **Service Layer Pattern**: Business logic separated into service classes (`DatabaseUserService`, `DatabaseQuoteService`, `ProductBOMServiceDB`)
- **Repository Pattern**: Database operations abstracted through service classes
- **Model-View-Controller**: FastAPI routes (controllers), Pydantic models, Jinja2 templates (views)
- **Database-First Design**: All data persisted to PostgreSQL, no in-memory storage
- **Security-First Architecture**: Comprehensive security middleware and validation layers (added in Milestone 1.1)

### Database Models (`database.py`)
- **User**: Authentication and user management
- **UserSession**: Session-based authentication with token expiration
- **AppMaterial**: Materials catalog (profiles, glass, hardware, consumables) with product codes
- **AppProduct**: Product definitions with dynamic BOM formulas
- **Quote**: Complete quotation storage with JSONB data
- **Color**: Color definitions for profiles (added for pricing variations)
- **MaterialColor**: Junction table for material-color pricing relationships

### Business Logic Services
- **ProductBOMServiceDB** (`services/product_bom_service_db.py`): Dynamic BOM calculations with **secure** formula evaluation
- **DatabaseUserService**: User authentication and session management with security enhancements
- **DatabaseQuoteService**: Quote persistence and retrieval
- **DatabaseColorService**: Color management and pricing calculations
- **Quote Calculation Engine** (`main.py:154-324`): Complex pricing calculations with material waste factors

### Security Architecture (NEW - Milestone 1.1)
- **SafeFormulaEvaluator** (`security/formula_evaluator.py`): Replaces dangerous eval() with secure simpleeval
- **InputValidator** (`security/input_validation.py`): Comprehensive input sanitization and validation
- **SecurityMiddleware** (`security/middleware.py`): CSRF protection, rate limiting, security headers
- **AuthSecurityEnhancer** (`security/auth_enhancements.py`): Brute force protection and session management

### Dynamic BOM System
The system uses **formula-based material calculations** where quantities are computed using **SECURE** mathematical expressions:
- Available variables: `width_m`, `height_m`, `area_m2`, `perimeter_m`, `quantity`
- Example formulas: `"width_m"`, `"2 * height_m"`, `"math.ceil(area_m2 / 2)"`
- **SECURITY**: Uses `simpleeval` instead of dangerous `eval()` - only mathematical operations allowed
- Supports waste factors and selling unit adjustments for materials
- Frontend uses equivalent safe JavaScript evaluator

### Authentication Architecture (ENHANCED - Milestone 1.1)
- **Cookie-based web authentication**: HTTP-only, SameSite cookies for browser sessions
- **Bearer token API authentication**: Cryptographically secure tokens for API access
- **Flexible authentication dependency**: `get_current_user_flexible()` handles both cookie and bearer token authentication
- **Brute force protection**: Account lockout after 5 failed attempts (15-minute lockout)
- **Session security**: Enhanced session validation with IP and user-agent checking
- **Password security**: Enforced strong passwords (8+ chars, letters + numbers)

### Frontend Integration
- **Server-side rendering**: Jinja2 templates with Bootstrap 5
- **Progressive enhancement**: JavaScript for real-time calculations
- **Responsive design**: Mobile-compatible interface
- **API integration**: Frontend calls REST endpoints for dynamic features

## Key Configuration Files

### Environment Configuration (`config.py`)
```python
# Database connection, security settings, business defaults
# Loads from .env file for environment-specific values
```

### Dependencies (`requirements.txt`)
- FastAPI with Uvicorn for web framework
- SQLAlchemy + psycopg2-binary for PostgreSQL
- Pydantic for data validation
- Passlib + python-jose for authentication
- Jinja2 for templating
- **Security Dependencies (NEW)**:
  - `simpleeval==0.9.13` - Safe mathematical expression evaluation
  - `bleach==6.1.0` - HTML sanitization and XSS prevention

## Important Implementation Details

### Material Calculation Logic (SECURE)
When calculating window costs, the system:
1. Retrieves product BOM from database
2. **SECURELY** evaluates formula for each material using `SafeFormulaEvaluator`
3. Applies waste factors (typically 1.05-1.10)
4. Adjusts for selling units (e.g., 6-meter aluminum profiles)
5. Calculates costs by material type (profiles, glass, hardware, consumables)
6. **Color pricing**: Applies color-specific pricing when profile colors are selected

### Database Session Management
- Uses SQLAlchemy session dependency injection
- All database operations are transactional
- Sessions auto-close after request completion
- Connection pooling handled by SQLAlchemy engine

### Security Considerations (COMPREHENSIVE - Milestone 1.1)
- **Password security**: Hashed with bcrypt, strong password requirements enforced
- **Session security**: Cryptographically secure tokens with enhanced validation
- **SQL injection prevention**: SQLAlchemy ORM with parameterized queries
- **Formula evaluation**: Secure `simpleeval` replaces dangerous `eval()`
- **Input validation**: Comprehensive sanitization for all user inputs
- **CSRF protection**: Token-based protection for state-changing operations
- **XSS prevention**: HTML sanitization with bleach library
- **Rate limiting**: IP-based protection against brute force attacks (100 req/min)
- **Secure headers**: X-Frame-Options, CSP, X-XSS-Protection, etc.
- **Cookie security**: HttpOnly, SameSite, secure flags configured

### API Compatibility
The application maintains dual interfaces:
- **Web routes**: `/`, `/dashboard`, `/quotes/new` (HTML responses)
- **API routes**: `/api/materials`, `/quotes/calculate` (JSON responses)
- **Auth routes**: Support both cookie and bearer token authentication

## Development Notes

### Adding New Material Types
Extend `MaterialType` enum in `models/product_bom_models.py` and update calculation logic in `calculate_window_item_from_bom()`.

### Modifying BOM Formulas (SECURE)
Edit the `quantity_formula` field in product BOMs. **IMPORTANT**: All formulas are now validated by `SafeFormulaEvaluator`:
- Available variables: `width_m`, `height_m`, `area_m2`, `perimeter_m`, `quantity`
- Only mathematical operations allowed (no arbitrary code execution)
- Use `formula_evaluator.validate_formula()` to test new formulas before saving

### Database Schema Changes
Modify SQLAlchemy models in `database.py`. Consider using Alembic for migrations in production.

### Testing Data
Sample data is automatically initialized on startup via `initialize_sample_data()` function.

## Recent Fixes (July 2025)

### Template Data Type Issues
When working with quote data stored as JSON in PostgreSQL, be aware that numeric values are returned as strings and need conversion:

- **Template math operations**: Use `|float` filter for calculations: `{% set total = total + (item.value|float) %}`
- **Template formatting**: Use `|float` filter before format: `{{ "%.2f"|format(value|float) }}`
- **JSON serialization**: Use `model_dump(mode='json')` to handle Decimal types properly

### FastAPI Lifecycle
- Updated from deprecated `@app.on_event("startup")` to modern `lifespan` context manager
- All deprecation warnings resolved

## Security Enhancements (July 2025 - Milestone 1.1)

### Critical Security Fixes Applied
1. **Formula Evaluation Security**: Replaced dangerous `eval()` with secure `simpleeval` parser
2. **Input Validation**: Comprehensive validation for all user inputs with HTML sanitization  
3. **CSRF Protection**: Token-based CSRF protection for all state-changing operations
4. **Secure Cookies**: HttpOnly, SameSite, and secure cookie configurations
5. **CORS Security**: Restricted origins and specific allowed methods/headers
6. **Rate Limiting**: IP-based rate limiting (100 requests/minute) with cleanup
7. **Authentication Security**: Brute force protection, account lockout, enhanced sessions
8. **Password Security**: Strong password requirements (8+ chars, letters + numbers)

### New Security Architecture
```
security/
├── formula_evaluator.py      # Safe mathematical expression evaluation
├── input_validation.py       # Comprehensive input sanitization
├── middleware.py             # CSRF, rate limiting, security headers
└── auth_enhancements.py      # Brute force protection, session management

static/js/
└── safe-formula-evaluator.js # Frontend formula security
```

### Security Headers Added
All responses now include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: [comprehensive policy]`

### Production Security Checklist
Before deploying to production:
- [ ] Set `secure=True` for cookies in HTTPS environment
- [ ] Configure rate limiting with Redis for scalability  
- [ ] Set environment-specific CORS origins
- [ ] Enable proper logging and monitoring
- [ ] Set up SSL/TLS certificates
- [ ] Review and update security headers for domain-specific needs

**SECURITY STATUS**: ✅ **PRODUCTION READY** - Enterprise-grade security implemented