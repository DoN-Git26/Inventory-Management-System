from unittest.mock import patch

import pytest

from app import app
from inventory_data import reset_products
from openfoodfacts import ExternalAPIError


@pytest.fixture(autouse=True)
def fresh_data():
    reset_products()
    yield
    reset_products()


@pytest.fixture
def client():
    return app.test_client()


def test_get_inventory(client):
    response = client.get("/inventory")
    assert response.status_code == 200
    assert len(response.get_json()) == 3


def test_get_single_item(client):
    response = client.get("/inventory/1")
    assert response.status_code == 200
    assert response.get_json()["product_name"] == "Fresh Milk 500ml"


def test_get_missing_item(client):
    assert client.get("/inventory/999").status_code == 404


def test_post_item(client):
    payload = {
        "product_name": "Milk",
        "brands": "Brookside",
        "barcode": "11111111",
        "quantity": 10,
        "price": 150,
        "category": "Dairy",
    }
    response = client.post("/inventory", json=payload)
    assert response.status_code == 201
    assert response.get_json()["id"] == 4
    assert len(client.get("/inventory").get_json()) == 4


def test_post_id_stays_unique_after_delete(client):
    client.delete("/inventory/2")
    response = client.post(
        "/inventory", json={"product_name": "Tea", "quantity": 1, "price": 1}
    )
    assert response.get_json()["id"] == 4


@pytest.mark.parametrize(
    "payload",
    [
        {"quantity": 1, "price": 1},
        {"product_name": "A", "quantity": -1, "price": 1},
        {"product_name": "A", "quantity": 1.5, "price": 1},
        {"product_name": "A", "quantity": 1, "price": "free"},
        {"product_name": " ", "quantity": 1, "price": 1},
        {"product_name": "A", "quantity": 1, "price": 1, "colour": "red"},
    ],
)
def test_post_rejects_invalid_data(client, payload):
    response = client.post("/inventory", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_post_rejects_non_json(client):
    assert client.post("/inventory", data="nope").status_code == 400


def test_patch_item(client):
    response = client.patch("/inventory/1", json={"price": 999})
    assert response.status_code == 200
    assert response.get_json()["price"] == 999
    assert client.get("/inventory/1").get_json()["price"] == 999


def test_patch_missing_item(client):
    assert client.patch("/inventory/999", json={"price": 1}).status_code == 404


@pytest.mark.parametrize("payload", [{}, {"price": -5}, {"id": 9}])
def test_patch_rejects_invalid_data(client, payload):
    assert client.patch("/inventory/1", json=payload).status_code == 400


def test_delete_item(client):
    response = client.delete("/inventory/2")
    assert response.status_code == 200
    assert client.get("/inventory/2").status_code == 404


def test_delete_missing_item(client):
    assert client.delete("/inventory/999").status_code == 404


@patch("app.get_product_by_barcode")
def test_barcode_lookup_route(mock_lookup, client):
    mock_lookup.return_value = {"product_name": "Mock Milk"}
    response = client.get("/inventory/barcode/123")
    assert response.status_code == 200
    assert response.get_json()["product_name"] == "Mock Milk"


@patch("app.get_product_by_barcode", return_value=None)
def test_barcode_lookup_not_found(_mock_lookup, client):
    assert client.get("/inventory/barcode/000").status_code == 404


@patch("app.get_product_by_barcode", side_effect=ExternalAPIError("down"))
def test_barcode_lookup_api_failure(_mock_lookup, client):
    assert client.get("/inventory/barcode/123").status_code == 502


@patch("app.get_product_by_barcode")
def test_add_api_product(mock_lookup, client):
    mock_lookup.return_value = {
        "product_name": "Mock Milk",
        "brands": "Mockco",
        "categories": "Dairy",
    }
    response = client.post("/inventory/barcode/123/add")
    assert response.status_code == 201
    item = response.get_json()
    assert item["product_name"] == "Mock Milk"
    assert item["barcode"] == "123"
    assert item["quantity"] == 0
    assert len(client.get("/inventory").get_json()) == 4


@patch("app.get_product_by_barcode", return_value=None)
def test_add_api_product_not_found(_mock_lookup, client):
    assert client.post("/inventory/barcode/000/add").status_code == 404
    assert len(client.get("/inventory").get_json()) == 3


@patch("app.search_products_by_name")
def test_name_search_route(mock_search, client):
    mock_search.return_value = [{"product_name": "Almond Milk", "code": "1"}]
    response = client.get("/inventory/search?name=almond")
    assert response.status_code == 200
    assert response.get_json()[0]["code"] == "1"


def test_name_search_requires_name(client):
    assert client.get("/inventory/search").status_code == 400
