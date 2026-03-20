#!/usr/bin/env python3
"""
Test Wallapop _next/data endpoint with proper search path.
"""

import httpx

headers = {
    'Accept': '*/*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

build_id = "6blW3FUOfPSACSay24qHZ"

# Try different URL patterns
urls = [
    f"https://es.wallapop.com/_next/data/{build_id}/es/search.json",
    f"https://es.wallapop.com/_next/data/{build_id}/es/app/search.json?keywords=bmw&category_id=100",
    f"https://es.wallapop.com/_next/data/{build_id}/es/search.json?keywords=bmw&category_id=100&order_by=newest",
]

for url in urls:
    print(f"Trying: {url}")
    response = httpx.get(url, headers=headers, follow_redirects=True)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            page_props = data.get('pageProps', {})
            print(f"  pageProps keys: {page_props.keys()}")

            # Look for any data that might contain search results
            for key in page_props.keys():
                val = page_props[key]
                if isinstance(val, dict) and ('item' in key or 'search' in key or 'result' in key):
                    print(f"  {key}: {len(val) if isinstance(val, (list, dict)) else type(val)}")
                elif isinstance(val, list) and len(val) > 0:
                    print(f"  {key}: list with {len(val)} items")
        except Exception as e:
            print(f"  Error: {e}")
    print()
