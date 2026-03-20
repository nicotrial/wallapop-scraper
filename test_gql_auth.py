#!/usr/bin/env python3
"""
Test Wallapop GraphQL endpoint with X-Signature authentication.
"""

import httpx
import json
from wallapop_auth import get_headers

url = "https://api.wallapop.com/gql/v1"

# Get auth headers
auth_headers = get_headers("POST", url)

headers = {
    'Accept': '*/*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Referer': 'https://es.wallapop.com/',
    'Origin': 'https://es.wallapop.com',
    'Content-Type': 'application/json',
    **auth_headers
}

# GraphQL query for search
query = {
    "operationName": "SearchItems",
    "variables": {
        "keywords": "bmw",
        "categoryIds": [100],
        "limit": 20
    },
    "query": """
    query SearchItems($keywords: String!, $categoryIds: [Int!], $limit: Int!) {
        searchItems(keywords: $keywords, categoryIds: $categoryIds, limit: $limit) {
            items {
                id
                title
                description
                price
                currency
            }
        }
    }
    """
}

print(f"Testing POST to: {url}")
print(f"Headers: {json.dumps(headers, indent=2)}")

try:
    response = httpx.post(url, headers=headers, json=query, timeout=10.0, follow_redirects=True)
    print(f"\nStatus: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Response: {response.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
