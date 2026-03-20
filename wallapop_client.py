"""
Wallapop API Client Module

Provides a client for searching items on Wallapop marketplace.
"""

import json
import time
from typing import Optional, Dict, Any, List
import httpx
from wallapop_auth import get_headers


BASE_URL = "https://api.wallapop.com/api/v3/general/search"
WEB_URL = "https://es.wallapop.com/api/v3/general/search"

# Category IDs
CATEGORY_CARS = 100
CATEGORY_CAR_PARTS = 107
CATEGORY_MOTORCYCLES = 129


class WallapopClient:
    """Client for interacting with the Wallapop API."""

    def __init__(self, delay: float = 2.0):
        """
        Initialize the client.

        Args:
            delay: Delay between requests in seconds (to avoid rate limiting)
        """
        self.delay = delay
        self._last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()

    def _build_search_url(
        self,
        keywords: str,
        category_id: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        distance_in_km: Optional[int] = None,
        order_by: str = "newest",
        time_filter: Optional[str] = None
    ) -> str:
        """
        Build the search URL with query parameters.

        Args:
            keywords: Search keywords (spaces will be converted to +)
            category_id: Category filter (e.g., 100 for cars)
            min_price: Minimum price in EUR
            max_price: Maximum price in EUR
            latitude: Location latitude
            longitude: Location longitude
            distance_in_km: Search radius in km
            order_by: Sort order (newest, price_low, price_high, closest)
            time_filter: Time filter (today, last_week)

        Returns:
            Complete URL string
        """
        params = []

        # Keywords (replace spaces with +)
        formatted_keywords = keywords.replace(' ', '+')
        params.append(f"keywords={formatted_keywords}")

        if category_id:
            params.append(f"category_id={category_id}")

        if min_price is not None:
            params.append(f"min_sale_price={min_price}")

        if max_price is not None:
            params.append(f"max_sale_price={max_price}")

        if latitude is not None:
            params.append(f"latitude={latitude}")

        if longitude is not None:
            params.append(f"longitude={longitude}")

        if distance_in_km is not None:
            params.append(f"distance_in_km={distance_in_km}")

        if order_by:
            params.append(f"order_by={order_by}")

        if time_filter:
            params.append(f"time_filter={time_filter}")

        return f"{BASE_URL}?{'&'.join(params)}"

    def search(
        self,
        keywords: str,
        category_id: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        distance_in_km: Optional[int] = None,
        order_by: str = "newest",
        time_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for items on Wallapop.

        Args:
            keywords: Search keywords
            category_id: Category filter
            min_price: Minimum price in EUR
            max_price: Maximum price in EUR
            latitude: Location latitude
            longitude: Location longitude
            distance_in_km: Search radius in km
            order_by: Sort order
            time_filter: Time filter

        Returns:
            JSON response from the API
        """
        url = self._build_search_url(
            keywords=keywords,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            latitude=latitude,
            longitude=longitude,
            distance_in_km=distance_in_km,
            order_by=order_by,
            time_filter=time_filter
        )

        return self._make_request(url)

    def search_cars(
        self,
        keywords: str = "coche proyecto",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        distance_in_km: Optional[int] = None,
        order_by: str = "newest"
    ) -> Dict[str, Any]:
        """
        Search for cars on Wallapop.

        Args:
            keywords: Search keywords (default: "coche proyecto")
            min_price: Minimum price in EUR
            max_price: Maximum price in EUR
            latitude: Location latitude
            longitude: Location longitude
            distance_in_km: Search radius in km
            order_by: Sort order

        Returns:
            JSON response from the API
        """
        return self.search(
            keywords=keywords,
            category_id=CATEGORY_CARS,
            min_price=min_price,
            max_price=max_price,
            latitude=latitude,
            longitude=longitude,
            distance_in_km=distance_in_km,
            order_by=order_by
        )

    def _make_request(self, url: str) -> Dict[str, Any]:
        """
        Make an authenticated request to the Wallapop API.

        Args:
            url: Full request URL

        Returns:
            JSON response as dictionary
        """
        self._rate_limit()

        headers = get_headers("GET", url)

        try:
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise WallapopAPIError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise WallapopAPIError(f"Request error: {e}")
        except json.JSONDecodeError as e:
            raise WallapopAPIError(f"JSON decode error: {e}")


class WallapopAPIError(Exception):
    """Exception raised for Wallapop API errors."""
    pass


def format_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant fields from a search result item.

    Args:
        item: Raw item from API response

    Returns:
        Formatted item with key fields
    """
    price_data = item.get('price', {})
    location_data = item.get('location', {})
    user_data = item.get('user', {})
    images = item.get('images', [])

    # Get main image URL
    image_url = None
    if images and len(images) > 0:
        image_url = images[0].get('urls', {}).get('medium') or images[0].get('urls', {}).get('small')

    return {
        'id': item.get('id'),
        'title': item.get('title'),
        'description': item.get('description', '')[:200] + '...' if len(item.get('description', '')) > 200 else item.get('description', ''),
        'price': price_data.get('amount'),
        'currency': price_data.get('currency'),
        'city': location_data.get('city'),
        'postal_code': location_data.get('postal_code'),
        'seller': user_data.get('micro_name'),
        'image_url': image_url,
        'url': f"https://es.wallapop.com/item/{item.get('slug', '')}" if item.get('slug') else None,
        'created_at': item.get('created_at')
    }


if __name__ == "__main__":
    # Test the client
    client = WallapopClient()

    print("Testing Wallapop client...")
    print(f"Searching for 'bmw e36'...")

    try:
        results = client.search_cars(
            keywords="bmw e36",
            max_price=5000
        )

        items = results.get('search_objects', [])
        print(f"\nFound {len(items)} items")

        if items:
            print("\nFirst result:")
            formatted = format_item(items[0])
            for key, value in formatted.items():
                print(f"  {key}: {value}")

    except WallapopAPIError as e:
        print(f"Error: {e}")
