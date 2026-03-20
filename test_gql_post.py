#!/usr/bin/env python3
"""
Test Wallapop GraphQL endpoint with POST request.
"""

import httpx
import json

headers = {
    'Accept': '*/*',
    'Accept-Language': 'es-ES,es;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Referer': 'https://es.wallapop.com/',
    'Origin': 'https://es.wallapop.com',
    'Content-Type': 'application/json',
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
                images {
                    urls {
                        medium
                    }
                }
                location {
                    city
                }
                user {
                    id
                    microName
                }
            }
        }
    }
    """
}

# Try different GraphQL endpoints
endpoints = [
    "https://api.wallapop.com/gql/v1",
    "https://es.wallapop.com/gql/v1",
    "https://www.wallapop.com/gql/v1",
]

for url in endpoints:
    print(f"Testing POST to: {url}")
    try:
        response = httpx.post(url, headers=headers, json=query, timeout=10.0, follow_redirects=True)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type')}")
        print(f"  Response: {response.text[:500]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
