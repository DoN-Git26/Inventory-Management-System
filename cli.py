from urllib.parse import urlencode

import requests

BASE_URL = "http://127.0.0.1:5000"


def api_request(method, path, payload=None):
    try:
        response = requests.request(
            method, f"{BASE_URL}{path}", json=payload, timeout=15
        )
    except requests.RequestException:
        print("Error: could not reach the inventory API. Is `python app.py` running?")
        return None
    try:
        data = response.json()
    except ValueError:
        print(f"Error: unexpected response from the API ({response.status_code})")
        return None
    if not response.ok:
        print(f"Error: {data.get('error', 'request failed')}")
        return None
    return data


def prompt_number(label, cast, optional=False):
    while True:
        raw = input(label).strip()
        if optional and not raw:
            return None
        try:
            value = cast(raw)
        except ValueError:
            print("Invalid number, please try again.")
            continue
        if value < 0:
            print("Value must not be negative.")
            continue
        return value


def format_item(item):
    return (
        f"[{item['id']}] {item['product_name']} ({item['brands']}) - "
        f"barcode: {item['barcode']}, qty: {item['quantity']}, "
        f"price: {item['price']}, category: {item['category']}"
    )


def view_inventory():
    items = api_request("GET", "/inventory")
    if items is None:
        return
    if not items:
        print("Inventory is empty.")
    for item in items:
        print(format_item(item))


def add_product():
    payload = {
        "product_name": input("Product Name: ").strip(),
        "brands": input("Brand: ").strip(),
        "barcode": input("Barcode: ").strip(),
        "quantity": prompt_number("Quantity: ", int),
        "price": prompt_number("Price: ", float),
        "category": input("Category: ").strip(),
    }
    item = api_request("POST", "/inventory", payload)
    if item:
        print("Added:", format_item(item))


def update_product():
    item_id = prompt_number("Product ID: ", int)
    quantity = prompt_number("New Quantity (blank to skip): ", int, optional=True)
    price = prompt_number("New Price (blank to skip): ", float, optional=True)
    payload = {}
    if quantity is not None:
        payload["quantity"] = quantity
    if price is not None:
        payload["price"] = price
    if not payload:
        print("Nothing to update.")
        return
    item = api_request("PATCH", f"/inventory/{item_id}", payload)
    if item:
        print("Updated:", format_item(item))


def delete_product():
    item_id = prompt_number("Product ID: ", int)
    result = api_request("DELETE", f"/inventory/{item_id}")
    if result:
        print(result["message"])


def lookup_barcode():
    barcode = input("Enter Barcode: ").strip()
    if not barcode:
        print("Barcode is required.")
        return
    product = api_request("GET", f"/inventory/barcode/{barcode}")
    if product:
        print(f"{product.get('product_name', 'Unknown')} - {product.get('brands', '')}")
        print(f"Ingredients: {product.get('ingredients_text', 'N/A')}")


def search_by_name():
    name = input("Enter Product Name: ").strip()
    if not name:
        print("Name is required.")
        return
    results = api_request("GET", f"/inventory/search?{urlencode({'name': name})}")
    for product in results or []:
        print(
            f"{product.get('code', '?')}: {product.get('product_name', 'Unknown')} "
            f"({product.get('brands', '')})"
        )


def add_product_from_api():
    barcode = input("Enter Barcode: ").strip()
    if not barcode:
        print("Barcode is required.")
        return
    item = api_request("POST", f"/inventory/barcode/{barcode}/add")
    if item:
        print("Added:", format_item(item))
        print("Use option 3 to set its price and quantity.")


ACTIONS = {
    "1": view_inventory,
    "2": add_product,
    "3": update_product,
    "4": delete_product,
    "5": lookup_barcode,
    "6": add_product_from_api,
    "7": search_by_name,
}


def menu():
    while True:
        print("\n===== INVENTORY SYSTEM =====")
        print("1. View Inventory")
        print("2. Add Product")
        print("3. Update Product")
        print("4. Delete Product")
        print("5. Lookup Product From API (barcode)")
        print("6. Add Product From API (barcode)")
        print("7. Search API By Name")
        print("8. Exit")

        choice = input("Choice: ").strip()
        if choice == "8":
            print("Goodbye")
            break
        action = ACTIONS.get(choice)
        if action:
            action()
        else:
            print("Invalid option")


if __name__ == "__main__":
    menu()
