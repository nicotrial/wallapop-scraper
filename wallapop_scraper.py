#!/usr/bin/env python3
"""
Wallapop Search Scraper using Playwright

Uses a headless browser to extract search results from the Wallapop web app.
This approach works around CloudFront API protection by using a real browser.
"""

import argparse
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class SearchResult:
    """Represents a Wallapop search result item."""
    id: str
    title: str
    description: str
    price: float
    currency: str
    city: str
    image_url: Optional[str]
    url: str
    seller: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WallapopScraper:
    """Scraper for Wallapop search results using Playwright."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None

    def _init_browser(self):
        """Initialize the browser if not already done."""
        if self._browser is None:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)

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
        max_results: int = 20
    ) -> List[SearchResult]:
        """Search for items on Wallapop."""
        self._init_browser()

        # Build search URL
        params = [f"keywords={keywords.replace(' ', '+')}"]

        if category_id:
            params.append(f"category_id={category_id}")
        if min_price:
            params.append(f"min_sale_price={min_price}")
        if max_price:
            params.append(f"max_sale_price={max_price}")
        if latitude:
            params.append(f"latitude={latitude}")
        if longitude:
            params.append(f"longitude={longitude}")
        if distance_in_km:
            params.append(f"distance_in_km={distance_in_km}")
        if order_by:
            params.append(f"order_by={order_by}")

        url = f"https://es.wallapop.com/app/search?{'&'.join(params)}"

        print(f"Navigating to: {url}")

        page = self._browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 800})

        # Store captured data
        captured_data = []

        # Intercept network responses
        def handle_response(response):
            try:
                if 'search' in response.url or 'catalog' in response.url:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'json' in content_type:
                            data = response.json()
                            captured_data.append((response.url, data))
                            print(f"  Captured: {response.url.split('/')[-1][:50]}...")
            except Exception:
                pass

        page.on("response", handle_response)

        try:
            # Navigate to the search page
            page.goto(url, wait_until="networkidle", timeout=30000)
            self._scroll_for_results(page, captured_data, max_results)

            # Try to extract from captured API data
            if captured_data:
                results = self._parse_api_data(captured_data, max_results)
                if results:
                    return results

            # Fallback: extract from DOM
            return self._extract_from_dom(page, max_results)

        finally:
            page.close()

    def _scroll_for_results(self, page, captured_data: List[tuple], max_results: int):
        """Scroll to trigger dynamic loading until enough results are captured."""
        previous_count = -1
        stable_rounds = 0

        for _ in range(8):
            current_count = self._count_captured_items(captured_data)
            if current_count >= max_results:
                return

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)

            new_count = self._count_captured_items(captured_data)
            if new_count == previous_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
            previous_count = new_count

            if stable_rounds >= 2:
                return

    def _parse_api_data(self, captured_data: List[tuple], max_results: int) -> List[SearchResult]:
        """Parse captured API responses."""
        merged_items = []
        seen_ids = set()

        for url, data in captured_data:
            items = self._extract_items_from_search_data(data)
            for item in items:
                if item.id and item.id in seen_ids:
                    continue
                if item.id:
                    seen_ids.add(item.id)
                merged_items.append(item)
                if len(merged_items) >= max_results:
                    return merged_items[:max_results]

        return merged_items[:max_results]

    def _extract_items_from_search_data(self, data: Dict) -> List[SearchResult]:
        """Extract items from search API response."""
        results = []

        # Try different possible structures
        search_objects = None

        # Structure 1: { search_objects: [...] }
        if 'search_objects' in data:
            search_objects = data['search_objects']

        # Structure 2: { data: { search_objects: [...] } }
        elif 'data' in data and isinstance(data['data'], dict):
            if 'search_objects' in data['data']:
                search_objects = data['data']['search_objects']
            elif 'section' in data['data'] and isinstance(data['data']['section'], dict):
                search_objects = data['data']['section'].get('items')

        if not search_objects:
            return results

        for item in search_objects:
            try:
                price_data = item.get('price', {})
                location_data = item.get('location', {})
                user_data = item.get('user', {})
                images = item.get('images', [])

                image_url = None
                if images and len(images) > 0:
                    image_url = images[0].get('urls', {}).get('medium') or images[0].get('urls', {}).get('small')

                results.append(SearchResult(
                    id=item.get('id', ''),
                    title=item.get('title', 'Unknown'),
                    description=item.get('description', '')[:200] if item.get('description') else '',
                    price=float(price_data.get('amount', 0)),
                    currency=price_data.get('currency', 'EUR'),
                    city=location_data.get('city', ''),
                    image_url=image_url,
                    url=self._build_item_url(item),
                    seller=user_data.get('micro_name', '') or item.get('user_id', '')
                ))
            except Exception:
                continue

        return results

    def _count_captured_items(self, captured_data: List[tuple]) -> int:
        """Count unique items across captured API responses."""
        seen_ids = set()
        for _, data in captured_data:
            for item in self._extract_items_from_search_data(data):
                if item.id:
                    seen_ids.add(item.id)
        return len(seen_ids)

    def _build_item_url(self, item: Dict[str, Any]) -> str:
        """Build an item URL from the current or legacy API fields."""
        slug = item.get('web_slug') or item.get('slug')
        if not slug:
            return ''
        return f"https://es.wallapop.com/item/{slug}"

    def _extract_from_dom(self, page, max_results: int) -> List[SearchResult]:
        """Extract results from the DOM as fallback."""
        print("Extracting from DOM...")

        selectors = [
            '[data-testid="item-card"]',
            'a[href*="/item/"]',
        ]

        items = []
        for selector in selectors:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"  Found {len(elements)} elements")
                for el in elements[:max_results]:
                    try:
                        title = el.inner_text().split('\n')[0] if el.inner_text() else 'Unknown'
                        link = el.get_attribute('href')

                        if link and '/item/' in link:
                            items.append(SearchResult(
                                id=link.split('/')[-1] if link else 'unknown',
                                title=title[:100],
                                description='',
                                price=0.0,
                                currency='EUR',
                                city='',
                                image_url=None,
                                url=f"https://es.wallapop.com{link}" if link.startswith('/') else link,
                                seller=''
                            ))
                    except Exception:
                        pass

                if items:
                    return items

        return []

    def search_cars(
        self,
        keywords: str = "coche proyecto",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        distance_in_km: Optional[int] = None,
        order_by: str = "newest",
        max_results: int = 20
    ) -> List[SearchResult]:
        """Search for cars on Wallapop."""
        return self.search(
            keywords=keywords,
            category_id=100,
            min_price=min_price,
            max_price=max_price,
            latitude=latitude,
            longitude=longitude,
            distance_in_km=distance_in_km,
            order_by=order_by,
            max_results=max_results
        )

    def close(self):
        """Close the browser and cleanup."""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def print_results(results: List[SearchResult]):
    """Print search results in a formatted way."""
    if not results:
        print("No results found.")
        return

    print(f"\n{'=' * 80}")
    print(f"Found {len(results)} results")
    print(f"{'=' * 80}\n")

    for i, item in enumerate(results, 1):
        print(f"[{i}] {item.title}")
        print(f"    Price: {item.price} {item.currency}")
        print(f"    Location: {item.city}")
        print(f"    Seller: {item.seller}")
        if item.description:
            print(f"    Description: {item.description[:150]}...")
        if item.url:
            print(f"    URL: {item.url}")
        print()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Scrape Wallapop search results with Playwright.")
    parser.add_argument("--query", default="bmw e36", help="Search query keywords.")
    parser.add_argument("--category-id", type=int, default=100, help="Wallapop category ID.")
    parser.add_argument("--min-price", type=int, help="Minimum price in EUR.")
    parser.add_argument("--max-price", type=int, default=5000, help="Maximum price in EUR.")
    parser.add_argument("--latitude", type=float, help="Latitude filter.")
    parser.add_argument("--longitude", type=float, help="Longitude filter.")
    parser.add_argument("--distance-km", type=int, help="Distance filter in km.")
    parser.add_argument("--order-by", default="newest", help="Sort order.")
    parser.add_argument("--max-results", type=int, default=20, help="Maximum number of results to return.")
    parser.add_argument("--headed", action="store_true", help="Run browser with a visible window.")
    parser.add_argument("--json", action="store_true", help="Print results as JSON.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    try:
        with WallapopScraper(headless=not args.headed) as scraper:
            results = scraper.search(
                keywords=args.query,
                category_id=args.category_id,
                min_price=args.min_price,
                max_price=args.max_price,
                latitude=args.latitude,
                longitude=args.longitude,
                distance_in_km=args.distance_km,
                order_by=args.order_by,
                max_results=args.max_results,
            )
            if args.json:
                print(json.dumps([item.to_dict() for item in results], indent=2, ensure_ascii=False))
            else:
                print_results(results)
    except ImportError as e:
        print(f"Error: {e}")
        print("\nPlease install Playwright:")
        print("  pip install playwright")
        print("  playwright install chromium")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
