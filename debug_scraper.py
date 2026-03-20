#!/usr/bin/env python3
"""
Debug the API response structure.
"""

import json
from playwright.sync_api import sync_playwright

url = "https://es.wallapop.com/app/search?keywords=bmw+e36&category_id=100&max_sale_price=5000"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    captured = []

    def handle_response(response):
        try:
            if 'search/section' in response.url:
                if response.status == 200:
                    data = response.json()
                    captured.append(data)
                    print(f"Captured from: {response.url}")
        except:
            pass

    page.on("response", handle_response)
    page.goto(url, wait_until="networkidle", timeout=30000)
    import time
    time.sleep(2)
    browser.close()

if captured:
    data = captured[0]
    print(f"\nTop-level keys: {list(data.keys())}")

    # Save full data for inspection
    with open('debug_search_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("Saved full data to debug_search_data.json")

    # Check for items
    if 'search_objects' in data:
        print(f"\nsearch_objects count: {len(data['search_objects'])}")
        if data['search_objects']:
            print(f"First item keys: {list(data['search_objects'][0].keys())}")
