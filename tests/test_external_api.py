from unittest.mock import patch

import pytest
import requests

from openfoodfacts import (
    ExternalAPIError,
    get_product_by_barcode,
    search_products_by_name,
)


@patch("requests.get")
def test_external_api(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "status": 1,
        "product": {"product_name": "Mock Milk"},
    }

    product = get_product_by_barcode("12345")

    assert product["product_name"] == "Mock Milk"
    assert "12345.json" in mock_get.call_args.args[0]


@patch("requests.get")
def test_product_not_found_status_zero(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"status": 0}
    assert get_product_by_barcode("000") is None


@patch("requests.get")
def test_product_not_found_404(mock_get):
    mock_get.return_value.status_code = 404
    assert get_product_by_barcode("000") is None


@patch("requests.get", side_effect=requests.Timeout)
def test_network_failure_raises(_mock_get):
    with pytest.raises(ExternalAPIError):
        get_product_by_barcode("123")


@patch("requests.get")
def test_server_error_raises(mock_get):
    mock_get.return_value.status_code = 500
    with pytest.raises(ExternalAPIError):
        get_product_by_barcode("123")


@patch("requests.get")
def test_invalid_json_raises(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.side_effect = ValueError
    with pytest.raises(ExternalAPIError):
        get_product_by_barcode("123")


@patch("requests.get")
def test_search_by_name(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "products": [{"product_name": "Almond Milk", "code": "1"}]
    }

    results = search_products_by_name("almond")

    assert results[0]["code"] == "1"
    assert mock_get.call_args.kwargs["params"]["search_terms"] == "almond"


@patch("requests.get")
def test_search_by_name_no_results(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"products": []}
    assert search_products_by_name("zzzz") == []
