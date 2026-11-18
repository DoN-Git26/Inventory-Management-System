# Inventory Management System

A Flask REST API inventory management system with:

- CRUD operations on an in-memory product list
- OpenFoodFacts API integration (lookup by barcode or name)
- An interactive CLI
- Pytest unit tests (external API calls are mocked)

Inventory lives in a Python list ([inventory_data.py](inventory_data.py)), so
changes reset whenever the server restarts.

## Project structure

```
Inventory-Management-System/
├── app.py              # Flask routes
├── inventory_data.py   # mock database (list of products)
├── openfoodfacts.py    # OpenFoodFacts API helpers
├── cli.py              # interactive CLI
├── requirements.txt
├── README.md
└── tests/
    ├── test_api.py
    ├── test_external_api.py
    └── test_cli.py
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Start the API

```bash
python app.py
```

The API runs at `http://127.0.0.1:5000` in Flask debug mode.

## Start the CLI

In a second terminal (with the API running):

```bash
python cli.py
```

Menu options:

```
1. View Inventory
2. Add Product
3. Update Product            (blank answers skip a field)
4. Delete Product
5. Lookup Product From API (barcode)
6. Add Product From API (barcode)
7. Search API By Name
8. Exit
```

Example session:

```
Choice: 5
Enter Barcode: 3017620422003
Nutella - Ferrero
Ingredients: Sugar, palm oil, hazelnuts ...

Choice: 6
Enter Barcode: 3017620422003
Added: [4] Nutella (Ferrero) - barcode: 3017620422003, qty: 0, price: 0, ...
```

Invalid numbers are re-prompted, and API or connection failures print a
friendly error instead of crashing.

## API endpoints

All bodies are JSON. Product fields: `id`, `product_name`, `brands`, `barcode`,
`quantity` (integer ≥ 0), `price` (number ≥ 0), `category`.

| Method | Path | Description | Status codes |
| --- | --- | --- | --- |
| GET | `/inventory` | List all items | 200 |
| GET | `/inventory/<id>` | Get one item | 200 / 404 |
| POST | `/inventory` | Add an item (`product_name`, `quantity`, `price` required) | 201 / 400 |
| PATCH | `/inventory/<id>` | Update any provided fields | 200 / 400 / 404 |
| DELETE | `/inventory/<id>` | Delete an item | 200 / 404 |
| GET | `/inventory/barcode/<barcode>` | Look up a product on OpenFoodFacts | 200 / 404 / 502 |
| GET | `/inventory/search?name=<text>` | Search OpenFoodFacts by name | 200 / 400 / 404 / 502 |
| POST | `/inventory/barcode/<barcode>/add` | Fetch a product and add it to inventory (quantity and price start at 0) | 201 / 404 / 502 |

`502` means OpenFoodFacts could not be reached or returned bad data.

Example:

```bash
curl -X POST http://127.0.0.1:5000/inventory \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Milk", "brands": "Brookside", "barcode": "111", "quantity": 10, "price": 150, "category": "Dairy"}'

curl -X PATCH http://127.0.0.1:5000/inventory/1 \
  -H "Content-Type: application/json" -d '{"price": 600}'
```

## Run tests

```bash
pytest
```
