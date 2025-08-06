<general_rules>
- Before creating new functions, search the `services/` directory to see if a similar one already exists.
- Security is a top priority in this repository. All code dealing with user input, authentication, or data processing must be written with security best practices in mind. Refer to the modules in the `security/` directory for existing patterns.
- When adding new material types, extend the `MaterialType` enum in `models/product_bom_models.py` and update the calculation logic accordingly.
- For database schema modifications, update the SQLAlchemy models in `database.py`.
- Run the application using `python main.py`.
- To test the database connection, run `python test_connection.py`.
</general_rules>
<repository_structure>
This is a FastAPI-based window quotation system with a PostgreSQL backend.

- **`main.py`**: The main entry point for the FastAPI application.
- **`database.py`**: Defines the SQLAlchemy database models.
- **`config.py`**: Manages application configuration, loading settings from an `.env` file.
- **`services/`**: Contains the core business logic, separated into service classes like `DatabaseUserService`, `DatabaseQuoteService`, and `ProductBOMServiceDB`.
- **`security/`**: Holds security-related modules, including input validation, formula evaluation, and middleware for CSRF protection and rate limiting.
- **`models/`**: Contains Pydantic models for data validation.
- **`templates/`**: Holds Jinja2 templates for server-side rendering of the frontend.
- **`static/`**: Contains static assets like CSS and JavaScript.
- **`tests/`**: Contains all automated tests.
- **`requirements.txt`**: Lists all Python dependencies.
</repository_structure>
<dependencies_and_installation>
- It is recommended to use a Python virtual environment. Create one with `python -m venv venv` and activate it.
- All Python dependencies are listed in `requirements.txt`.
- Install the dependencies by running: `pip install -r requirements.txt`.
- The core dependencies include FastAPI, SQLAlchemy, psycopg2-binary, Pydantic, and several security-focused libraries like `simpleeval` and `bleach`.
</dependencies_and_installation>
<testing_instructions>
- The project uses `pytest` for automated testing.
- Test files are located in the `tests/` directory.
- To run the entire test suite, execute `pytest` from the root directory of the project.
- The `pytest.ini` file contains the configuration for `pytest`, including test discovery patterns and custom markers.
- Available markers include `unit`, `integration`, `security`, `performance`, `csv`, and `api`. You can run specific tests using the `-m` flag, for example: `pytest -m security`.
- There is also a dedicated script, `run_csv_tests.py`, for running tests related to CSV functionality.
</testing_instructions>
<pull_request_formatting>
</pull_request_formatting>

