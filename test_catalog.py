#!/usr/bin/env python3
"""
Test Wallapop catalog endpoint (used by web app).
"""

import httpx
import json

# Try the catalog endpoint used by the web app
urls = [
    "https://es.wallapop.com/app/catalog/search?keywords=bmw&category_ids=100",
    "https://api.wallapop.com/api/v3/catalog/search?keywords=bmw&category_ids=100",
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
        if response.status_code == 200:
            data = response.json()
            print(f"  SUCCESS! Items found: {len(data.get('data', {}).get('items', []))}")
        else:
            print(f"  Response: {response.text[:300]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
