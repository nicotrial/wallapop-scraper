#!/usr/bin/env python3
"""
Test Wallapop _next/data endpoint (Next.js data fetching).
"""

import httpx
import re

headers = {
    'Accept': '*/*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

# Get the main page to find the build ID
print("Fetching main page...")
response = httpx.get("https://es.wallapop.com/app/search?keywords=bmw&category_id=100", headers=headers, follow_redirects=True)
print(f"Status: {response.status_code}")

# Try to find the build ID
build_id_match = re.search(r'"buildId":"([^"]+)"', response.text)
if build_id_match:
    build_id = build_id_match.group(1)
    print(f"Found build ID: {build_id}")

    # Try the _next/data endpoint
    next_url = f"https://es.wallapop.com/_next/data/{build_id}/es/search.json?keywords=bmw&category_id=100"
    print(f"\nTrying: {next_url}")
    response = httpx.get(next_url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")

    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Success! Got JSON data")
            print(f"Keys: {data.keys()}")
            print(f"\npageProps keys: {data.get('pageProps', {}).keys()}")

            # Check for search results
            search_data = data.get('pageProps', {}).get('search', {})
            print(f"\nsearch keys: {search_data.keys()}")

            items = search_data.get('items', [])
            print(f"\nFound {len(items)} items")

            if items:
                print(f"\nFirst item keys: {items[0].keys()}")
                print(f"First item title: {items[0].get('title')}")
                print(f"First item price: {items[0].get('price')}")
        except Exception as e:
            print(f"Not JSON: {e}")
            print(f"Preview: {response.text[:500]}")
else:
    print("Could not find build ID")
