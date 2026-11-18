import requests

BASE_URL = "https://world.openfoodfacts.org/api/v0/product"
SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
HEADERS = {"User-Agent": "InventoryManagementSystem/1.0 (educational project)"}
TIMEOUT = 10


class ExternalAPIError(Exception):
    pass


def _get_json(url, **kwargs):
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kwargs)
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise ExternalAPIError(f"OpenFoodFacts returned {response.status_code}")
        data = response.json()
    except requests.RequestException as error:
        raise ExternalAPIError("OpenFoodFacts is unreachable") from error
    except ValueError as error:
        raise ExternalAPIError("OpenFoodFacts returned invalid JSON") from error
    if not isinstance(data, dict):
        raise ExternalAPIError("OpenFoodFacts returned an unexpected response")
    return data


def get_product_by_barcode(barcode):
    data = _get_json(f"{BASE_URL}/{barcode}.json")
    if data is None or data.get("status") != 1:
        return None
    return data.get("product")


def search_products_by_name(name, limit=5):
    data = _get_json(
        SEARCH_URL,
        params={"search_terms": name, "json": 1, "page_size": limit},
    )
    results = (data or {}).get("products", [])
    return results if isinstance(results, list) else []
