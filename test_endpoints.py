#!/usr/bin/env python3
"""
Test different Wallapop API endpoints to find one that works.
"""

import httpx
from wallapop_auth import get_headers

# Test different endpoints
endpoints = [
    "https://api.wallapop.com/api/v3/general/search?keywords=bmw&category_id=100",
    "https://es.wallapop.com/api/v3/general/search?keywords=bmw&category_id=100",
    "https://www.wallapop.com/api/v3/general/search?keywords=bmw&category_id=100",
]

headers_base = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Referer': 'https://es.wallapop.com/',
    'Origin': 'https://es.wallapop.com',
    'Sec-Ch-Ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"macOS"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Connection': 'keep-alive',
}

print("Testing Wallapop endpoints...\n")

for url in endpoints:
    print(f"Testing: {url}")
    try:
        # First try without auth headers
        print("  Without auth...")
        response = httpx.get(url, headers=headers_base, timeout=10.0, follow_redirects=True)
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            print(f"    SUCCESS!")
            print(f"    Response preview: {response.text[:200]}")
        else:
            print(f"    Response: {response.text[:200]}")
    except Exception as e:
        print(f"    Error: {e}")

    try:
        # Then try with auth headers
        print("  With auth headers...")
        auth_headers = get_headers("GET", url)
        headers = {**headers_base, **auth_headers}
        response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            print(f"    SUCCESS!")
            print(f"    Response preview: {response.text[:200]}")
        else:
            print(f"    Response: {response.text[:200]}")
    except Exception as e:
        print(f"    Error: {e}")

    print()
