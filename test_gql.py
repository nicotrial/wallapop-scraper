#!/usr/bin/env python3
"""
Test Wallapop GraphQL/search endpoints.
"""

import httpx

# Try various endpoints
urls = [
    "https://es.wallapop.com/api/v3/general/search?keywords=bmw&category_id=100",
    "https://es.wallapop.com/_next/data/search?keywords=bmw&category_id=100",
    "https://api.wallapop.com/gql/search?keywords=bmw&category_id=100",
]

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Referer': 'https://es.wallapop.com/',
}

for url in urls:
    print(f"Testing: {url}")
    try:
        response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type')}")
        if response.status_code == 200:
            print(f"  SUCCESS!")
        print()
    except Exception as e:
        print(f"  Error: {e}\n")
