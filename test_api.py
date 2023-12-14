import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, Base, get_db
from models import Product
from unittest.mock import patch

SQLALCHEMY_TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost/db_vending_machine_test"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency override to get the test database session
@pytest.fixture(scope="module")
def override_dependency():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    # Teardown/cleanup step after the tests are completed
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db)


@pytest.fixture(scope="module")
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_redis():
    with patch('main.r.get') as mock_get, patch('main.r.set') as mock_set:
        yield mock_get, mock_set


# Create test tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_create_product(override_dependency):
    data = {
        "name": "Test Product",
        "price": 2000
    }
    response = client.post("/products/", json=data)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["id"]
    assert response_json["name"] == data["name"]
    assert response_json["price"] == data["price"]
    return response_json


def test_get_product(override_dependency, db):
    # Creating a session within the function scope
    new_product = Product(name='aqua', price=2000)
    db.add(new_product)
    db.commit()

    response = client.get(f"/products/{new_product.id}")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["name"] == new_product.name
    assert response_json["price"] == new_product.price
    assert response_json["id"] == new_product.id


def test_update_product(override_dependency, db):
    new_product = Product(name='aqua', price=2000)
    db.add(new_product)
    db.commit()
    product_instance = new_product

    data = {
        "name": "Updated Test Product",
        "price": 5000
    }

    response = client.put(f"/products/{product_instance.id}", json=data)
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["name"] == data['name']
    assert response_json["price"] == data['price']
    assert response_json["id"] == product_instance.id


def test_get_all_products():
    response = client.get("/products/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_delete_product(override_dependency, db):
    new_product = Product(name='aqua', price=2000)
    db.add(new_product)
    db.commit()
    response = client.delete(f"/products/{new_product.id}")
    assert response.status_code == 200


def test_machine_process_money_no_ongoing_process(mock_redis):
    mock_get, mock_set = mock_redis
    mock_get.return_value = None

    payload = {"amount": 5000}
    response = client.post("/machine-process-money/", json=payload)

    assert response.status_code == 200
    assert "process" in response.json()
    assert "productPurchaseAble" in response.json()


def test_machine_process_money_ongoing_process(mock_redis):
    mock_get, mock_set = mock_redis
    mock_get.return_value = json.dumps({
        "process": "some_uuid",
        "amount": 5000,
        "products": []
    }).encode('utf-8')

    payload = {"amount": 5000}
    response = client.post("/machine-process-money/", json=payload)

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "product_list": [],
            "description": "machine still process money. select product to buy"
        }
    }


def test_purchase_with_machine_process(mock_redis):
    mock_get, mock_delete = mock_redis
    mock_get.return_value = json.dumps({
        "process": "some_uuid",
        "amount": 10000,
        "products": [
            {"id": 1, "name": "Product 1", "price": 5000},
            {"id": 2, "name": "Product 2", "price": 3000}
        ]
    }).encode('utf-8')

    process_id = "some_uuid"
    selected_product_index = 0  # Choose the first product

    response = client.get(f"/purchase/{process_id}/{selected_product_index}")

    assert response.status_code == 200
    expected_response = {
        "selected_product_name": "Product 1",
        "amount": 10000,
        "quantity": "2",
        "output": "2 Product 1"
    }
    assert response.json() == expected_response
