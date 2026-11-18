from flask import Flask, jsonify, request

from inventory_data import products
from openfoodfacts import (
    ExternalAPIError,
    get_product_by_barcode,
    search_products_by_name,
)

app = Flask(__name__)

FIELDS = ("product_name", "brands", "barcode", "quantity", "price", "category")
REQUIRED_FIELDS = ("product_name", "quantity", "price")
TEXT_FIELDS = ("product_name", "brands", "barcode", "category")


def find_item(item_id):
    return next((p for p in products if p["id"] == item_id), None)


def next_id():
    return max((p["id"] for p in products), default=0) + 1


def validate(data, partial=False):
    if not isinstance(data, dict):
        return "Request body must be a JSON object"
    unknown = set(data) - set(FIELDS)
    if unknown:
        return f"Unknown field(s): {', '.join(sorted(unknown))}"
    if partial and not data:
        return "At least one field is required"
    if not partial:
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        if missing:
            return f"Missing required field(s): {', '.join(missing)}"
    for field in TEXT_FIELDS:
        if field in data and not isinstance(data[field], str):
            return f"{field} must be a string"
    if "product_name" in data and not data["product_name"].strip():
        return "product_name must not be empty"
    price = data.get("price", 0)
    if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
        return "price must be a non-negative number"
    quantity = data.get("quantity", 0)
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
        return "quantity must be a non-negative integer"
    return None


def external_error(error):
    return jsonify({"error": str(error)}), 502


@app.route("/inventory", methods=["GET"])
def get_inventory():
    return jsonify(products), 200


@app.route("/inventory/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item), 200


@app.route("/inventory", methods=["POST"])
def add_item():
    data = request.get_json(silent=True)
    error = validate(data)
    if error:
        return jsonify({"error": error}), 400

    new_item = {
        "id": next_id(),
        "product_name": data["product_name"],
        "brands": data.get("brands", ""),
        "barcode": data.get("barcode", ""),
        "quantity": data["quantity"],
        "price": data["price"],
        "category": data.get("category", ""),
    }
    products.append(new_item)
    return jsonify(new_item), 201


@app.route("/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404

    updates = request.get_json(silent=True)
    error = validate(updates, partial=True)
    if error:
        return jsonify({"error": error}), 400

    item.update(updates)
    return jsonify(item), 200


@app.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = find_item(item_id)
    if item is None:
        return jsonify({"error": "Item not found"}), 404
    products.remove(item)
    return jsonify({"message": "Item deleted successfully"}), 200


@app.route("/inventory/barcode/<barcode>", methods=["GET"])
def barcode_lookup(barcode):
    try:
        product = get_product_by_barcode(barcode)
    except ExternalAPIError as error:
        return external_error(error)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200


@app.route("/inventory/search", methods=["GET"])
def name_lookup():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"error": "name query parameter is required"}), 400
    try:
        results = search_products_by_name(name)
    except ExternalAPIError as error:
        return external_error(error)
    if not results:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(results), 200


@app.route("/inventory/barcode/<barcode>/add", methods=["POST"])
def add_api_product(barcode):
    try:
        product = get_product_by_barcode(barcode)
    except ExternalAPIError as error:
        return external_error(error)
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    new_item = {
        "id": next_id(),
        "product_name": product.get("product_name") or "Unknown Product",
        "brands": product.get("brands") or "Unknown Brand",
        "barcode": barcode,
        "quantity": 0,
        "price": 0,
        "category": product.get("categories") or "Unknown",
    }
    products.append(new_item)
    return jsonify(new_item), 201


if __name__ == "__main__":
    app.run(debug=True)
