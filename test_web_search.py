#!/usr/bin/env python3
"""
Extract search data from Wallapop web app page source.
"""

import httpx
import re
import json

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
}

# Get the search page
url = "https://es.wallapop.com/app/search?keywords=bmw&category_id=100&order_by=newest"
print(f"Fetching: {url}")

response = httpx.get(url, headers=headers, follow_redirects=True)
print(f"Status: {response.status_code}")

# Look for embedded data in the page
# Check for __NEXT_DATA__ or similar
next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', response.text, re.DOTALL)
if next_data_match:
    print("Found __NEXT_DATA__")
    try:
        data = json.loads(next_data_match.group(1))
        print(f"Keys: {data.keys()}")
        print(f"\nprops keys: {data.get('props', {}).keys()}")
        print(f"page: {data.get('page')}")
        print(f"query: {data.get('query')}")

        # Check pageProps
        page_props = data.get('props', {}).get('pageProps', {})
        print(f"\npageProps keys: {page_props.keys()}")

        for key in page_props.keys():
            val = page_props[key]
            if isinstance(val, (list, dict)):
                print(f"  {key}: {type(val).__name__} with {len(val) if isinstance(val, list) else len(val.keys())} items")
            else:
                print(f"  {key}: {type(val).__name__}")
    except Exception as e:
        print(f"Error parsing: {e}")

# Look for any script tags with data
script_matches = re.findall(r'<script[^>]*>(.*?)</script>', response.text, re.DOTALL)
print(f"\nFound {len(script_matches)} script tags")

# Check for window.__INITIAL_STATE__ or similar
initial_state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', response.text, re.DOTALL)
if initial_state_match:
    print("Found __INITIAL_STATE__")
else:
    print("No __INITIAL_STATE__ found")

# Look for any JSON data that might contain search results
json_matches = re.findall(r'"search_objects"|"items":\s*\[', response.text)
print(f"Found {len(json_matches)} potential JSON data references")

# Save page for inspection
with open('search_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text[:50000])
print("\nSaved first 50KB of page to search_page.html")
