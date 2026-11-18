import copy

DEFAULT_PRODUCTS = [
    {
        "id": 1,
        "product_name": "Fresh Milk 500ml",
        "brands": "Brookside",
        "barcode": "1234567890123",
        "quantity": 50,
        "price": 65,
        "category": "Dairy Products",
    },
    {
        "id": 2,
        "product_name": "Maize Flour 2kg",
        "brands": "Jogoo",
        "barcode": "2345678901234",
        "quantity": 120,
        "price": 190,
        "category": "Flours and Grains",
    },
    {
        "id": 3,
        "product_name": "Tea Leaves 250g",
        "brands": "Ketepa Pride",
        "barcode": "3456789012345",
        "quantity": 80,
        "price": 140,
        "category": "Beverages",
    },
]

products = copy.deepcopy(DEFAULT_PRODUCTS)


def reset_products():
    products[:] = copy.deepcopy(DEFAULT_PRODUCTS)
