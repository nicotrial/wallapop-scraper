#!/usr/bin/env python3
"""
Test Wallapop catalog endpoint with proper decoding.
"""

import httpx

url = "https://es.wallapop.com/app/catalog/search?keywords=bmw&category_ids=100"

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Referer': 'https://es.wallapop.com/',
}

print(f"Testing: {url}")
response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")
print(f"Content length: {len(response.content)}")
print(f"\nFirst 500 chars:\n{response.text[:500]}")
