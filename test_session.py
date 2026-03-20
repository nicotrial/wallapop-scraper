#!/usr/bin/env python3
"""
Test Wallapop with session cookies.
"""

import httpx

# First get a session
session_url = "https://es.wallapop.com/"

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

# Get initial session
print("Getting session...")
client = httpx.Client(follow_redirects=True)
response = client.get(session_url, headers=headers, timeout=10.0)
print(f"Session status: {response.status_code}")
print(f"Cookies: {client.cookies}")

# Now try the search
search_url = "https://es.wallapop.com/api/v3/general/search?keywords=bmw&category_id=100"
print(f"\nSearching: {search_url}")
response = client.get(search_url, headers=headers, timeout=10.0)
print(f"Search status: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")

if response.status_code == 200:
    try:
        data = response.json()
        print(f"Items found: {len(data.get('search_objects', []))}")
    except:
        print(f"Response: {response.text[:500]}")
else:
    print(f"Response: {response.text[:500]}")

client.close()
