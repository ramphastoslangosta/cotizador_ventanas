<general_rules>
- Before creating new functions, especially within the `services` or `models` directories, always search for existing implementations to promote code reuse.
- The main entry point for the application is `main.py`. For debugging, you can use `debug_main.py` and `debug_env.py`.
- To test the database connection, run the `test_connection.py` script.
- The application follows a security-first architecture. A key aspect of this is the use of `simpleeval` for securely evaluating mathematical formulas, avoiding the risks of `eval()`.
- The project is built on a FastAPI-based window quotation system and utilizes key architectural patterns such as the Service Layer Pattern, Repository Pattern, and Model-View-Controller (MVC).
- Commonly executed scripts:
  - To run the application: `python main.py`
  - To install dependencies: `pip install -r requirements.txt`
  - To set up a virtual environment: `python -m venv venv` and `source venv/bin/activate` (or `venv\Scripts\activate` on Windows).
</general_rules>
<repository_structure>
The repository is structured as a FastAPI application with a clear separation of concerns. Key directories include:
- `main.py`: The main entry point of the FastAPI application.
- `models/`: Contains Pydantic models for data validation and serialization.
- `services/`: Holds the business logic and service layer implementations.
- `security/`: Implements enterprise-grade security features, including authentication, authorization, and secure formula evaluation.
- `error_handling/`: Contains modules for comprehensive error handling and application resilience.
- `data_protection/`: Includes features for data protection, such as audit trails and backups.
- `static/`: Stores static files like CSS, JavaScript, and images.
- `templates/`: Contains Jinja2 templates for server-side rendering of HTML.
- `tests/`: Includes all tests for the application.
</repository_structure>
<dependencies_and_installation>
- Dependencies are managed using `pip` and the `requirements.txt` file.
- To install all required packages, run the following command in your terminal:
  ```bash
  pip install -r requirements.txt
  ```
- It is recommended to use a Python virtual environment (`venv`) to manage project dependencies. You can create one by running `python -m venv venv`.
</dependencies_and_installation>
<testing_instructions>
- The project uses `pytest` as its testing framework.
- Tests are located in the `tests/` directory.
- To run all tests, you can execute `pytest` from the root directory.
- For specific sets of tests, such as the CSV-related tests, you can use the provided script: `python run_csv_tests.py`.
- The `pytest.ini` file defines several markers to categorize tests, including `unit`, `integration`, `security`, `csv`, and `api`. You can run tests of a specific category using the `-m` flag (e.g., `pytest -m unit`).
- The testing strategy relies heavily on mocking, particularly for database sessions and external services, to ensure that tests are fast and isolated.
</testing_instructions>
<pull_request_formatting>
</pull_request_formatting>

