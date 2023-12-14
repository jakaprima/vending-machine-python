# FastAPI Project Vending Machine, based on python stack with Unit Tests

## Setup

1. **Installation**
Ensure you have Python installed. Then, install the required dependencies using pip:
```bash
pip install -r requirements.txt
```
2. **Running the Application**
Start the FastAPI application using Uvicorn:
```bash
uvicorn main:app --reload
```
3. **Running Tests**
Run the unit tests using `pytest`:
```bash
pytest
```

4. **Linting with `flake8`**

To maintain code quality and adhere to PEP 8 style guide, use `flake8` for linting:

- Install `flake8`:

  ```
  pip install flake8
  ```

- Run `flake8` on your Python files or directories:

  ```
  flake8 .
  ```

## Project Structure

- `main.py`: Contains the FastAPI application setup and API endpoints.
- `test_api.py`: Unit tests for testing the API endpoints.
- `requirements.txt`: Contains the required Python packages.
- `.flake8`: Configuration file for `flake8` to define linting rules.

## Usage

- The FastAPI application provides endpoints for CRUD operations on items.
- Unit tests validate the functionality of these endpoints using Faker for generating random data.


## Contributing

Feel free to contribute by opening issues or creating pull requests.

## License

This project is licensed under the MIT License.







