#!/usr/bin/env python3
"""
Test different Wallapop API paths to find working search endpoint.
"""

import httpx
import json

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Referer': 'https://es.wallapop.com/',
    'Origin': 'https://es.wallapop.com',
}

# Try various API paths that might work
base_urls = [
    "https://es.wallapop.com",
    "https://www.wallapop.com",
    "https://api.wallapop.com",
]

paths = [
    "/api/v3/search",
    "/api/v3/catalog/search",
    "/api/v3/items/search",
    "/api/v3/general/search",
    "/gql/v1",
]

query = "?keywords=bmw&category_id=100"

for base in base_urls:
    for path in paths:
        url = f"{base}{path}{query}"
        print(f"Testing: {url}")
        try:
            response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type')}")

            if response.status_code == 200 and 'json' in response.headers.get('content-type', ''):
                try:
                    data = response.json()
                    print(f"  SUCCESS! JSON response with keys: {list(data.keys())[:5]}")
                    # Save this working endpoint
                    with open('working_endpoint.txt', 'w') as f:
                        f.write(f"{url}\n{json.dumps(data, indent=2)[:1000]}")
                except:
                    print(f"  Not valid JSON")
        except Exception as e:
            print(f"  Error: {e}")
        print()
