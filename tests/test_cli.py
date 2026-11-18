from unittest.mock import MagicMock, patch

import requests

import cli


def fake_response(data, ok=True, status=200):
    response = MagicMock()
    response.ok = ok
    response.status_code = status
    response.json.return_value = data
    return response


ITEM = {
    "id": 1,
    "product_name": "Milk",
    "brands": "Brand",
    "barcode": "123",
    "quantity": 5,
    "price": 10,
    "category": "Dairy",
}


@patch("cli.requests.request")
def test_api_request_returns_json(mock_request):
    mock_request.return_value = fake_response([ITEM])
    assert cli.api_request("GET", "/inventory") == [ITEM]


@patch("cli.requests.request")
def test_api_request_reports_api_error(mock_request, capsys):
    mock_request.return_value = fake_response(
        {"error": "Item not found"}, ok=False, status=404
    )
    assert cli.api_request("GET", "/inventory/9") is None
    assert "Item not found" in capsys.readouterr().out


@patch("cli.requests.request", side_effect=requests.ConnectionError)
def test_api_request_handles_unreachable_server(_mock_request, capsys):
    assert cli.api_request("GET", "/inventory") is None
    assert "could not reach" in capsys.readouterr().out


@patch("cli.requests.request")
def test_view_inventory_prints_items(mock_request, capsys):
    mock_request.return_value = fake_response([ITEM])
    cli.view_inventory()
    assert "Milk" in capsys.readouterr().out


@patch("cli.requests.request")
def test_add_product_sends_typed_payload(mock_request):
    mock_request.return_value = fake_response(ITEM, status=201)
    answers = ["Milk", "Brand", "123", "5", "10.5", "Dairy"]
    with patch("builtins.input", side_effect=answers):
        cli.add_product()
    payload = mock_request.call_args.kwargs["json"]
    assert payload["quantity"] == 5
    assert payload["price"] == 10.5


def test_prompt_number_retries_on_invalid_input(capsys):
    with patch("builtins.input", side_effect=["abc", "-3", "7"]):
        assert cli.prompt_number("Qty: ", int) == 7
    output = capsys.readouterr().out
    assert "Invalid number" in output
    assert "negative" in output


@patch("cli.requests.request")
def test_update_product_only_sends_provided_fields(mock_request):
    mock_request.return_value = fake_response(ITEM)
    with patch("builtins.input", side_effect=["1", "", "99"]):
        cli.update_product()
    assert mock_request.call_args.args[:2] == ("PATCH", f"{cli.BASE_URL}/inventory/1")
    assert mock_request.call_args.kwargs["json"] == {"price": 99.0}


@patch("cli.requests.request")
def test_update_product_with_no_changes_skips_request(mock_request, capsys):
    with patch("builtins.input", side_effect=["1", "", ""]):
        cli.update_product()
    mock_request.assert_not_called()
    assert "Nothing to update" in capsys.readouterr().out


@patch("cli.requests.request")
def test_delete_product(mock_request, capsys):
    mock_request.return_value = fake_response({"message": "Item deleted successfully"})
    with patch("builtins.input", side_effect=["1"]):
        cli.delete_product()
    assert mock_request.call_args.args[0] == "DELETE"
    assert "deleted" in capsys.readouterr().out


@patch("cli.requests.request")
def test_search_by_name_encodes_query(mock_request, capsys):
    mock_request.return_value = fake_response(
        [{"code": "1", "product_name": "Almond Milk", "brands": "Silk"}]
    )
    with patch("builtins.input", side_effect=["almond milk"]):
        cli.search_by_name()
    assert mock_request.call_args.args[1].endswith("/inventory/search?name=almond+milk")
    assert "Almond Milk" in capsys.readouterr().out


@patch("cli.requests.request")
def test_add_product_from_api(mock_request, capsys):
    mock_request.return_value = fake_response(ITEM, status=201)
    with patch("builtins.input", side_effect=["123"]):
        cli.add_product_from_api()
    assert mock_request.call_args.args[:2] == (
        "POST",
        f"{cli.BASE_URL}/inventory/barcode/123/add",
    )
    assert "Added" in capsys.readouterr().out


def test_menu_handles_invalid_option_and_exit(capsys):
    with patch("builtins.input", side_effect=["x", "8"]):
        cli.menu()
    output = capsys.readouterr().out
    assert "Invalid option" in output
    assert "Goodbye" in output
