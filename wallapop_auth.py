"""
Wallapop API Authentication Module

Handles X-Signature generation for Wallapop API requests.
Uses HMAC-SHA256 with a reverse-engineered secret key.
"""

import hmac
import hashlib
import base64
import time


# React app secret key (Base64 encoded)
# Decodes to: "Now that you've found this, are you ready to join us? jobs@wallapop.com"
SECRET_KEY = "Tm93IHRoYXQgeW91J3ZlIGZvdW5kIHRoaXMsIGFyZSB5b3UgcmVhZHkgdG8gam9pbiB1cz8gam9ic0B3YWxsYXBvcC5jb20=="


def get_secret_key() -> bytes:
    """Decode the Base64 encoded secret key."""
    return base64.b64decode(SECRET_KEY)


def generate_signature(method: str, url: str, timestamp: str = None) -> str:
    """
    Generate X-Signature header for Wallapop API requests.

    The signature format is: METHOD|URL|TIMESTAMP|
    This string is then hashed with HMAC-SHA256 and Base64 encoded.

    Args:
        method: HTTP method (e.g., 'GET', 'POST')
        url: Full request URL including query parameters
        timestamp: Unix epoch timestamp in seconds (auto-generated if None)

    Returns:
        Base64-encoded HMAC-SHA256 signature
    """
    if timestamp is None:
        timestamp = str(int(time.time()))

    # Build signature string: METHOD|URL|TIMESTAMP|
    signature_string = f"{method.upper()}|{url}|{timestamp}|"

    # Create HMAC-SHA256 hash
    secret = get_secret_key()
    signature = hmac.new(
        secret,
        signature_string.encode('utf-8'),
        hashlib.sha256
    ).digest()

    # Return Base64 encoded signature
    return base64.b64encode(signature).decode('utf-8')


def get_headers(method: str, url: str) -> dict:
    """
    Generate complete headers for a Wallapop API request.

    Args:
        method: HTTP method
        url: Full request URL

    Returns:
        Dictionary of headers to include in the request
    """
    timestamp = str(int(time.time()))
    signature = generate_signature(method, url, timestamp)

    return {
        'X-Signature': signature,
        'X-Timestamp': timestamp,
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


if __name__ == "__main__":
    # Test signature generation
    test_url = "https://api.wallapop.com/api/v3/general/search?keywords=test"
    test_timestamp = "1742480000"

    sig = generate_signature("GET", test_url, test_timestamp)
    print(f"Test URL: {test_url}")
    print(f"Timestamp: {test_timestamp}")
    print(f"Signature: {sig}")

    # Generate headers
    headers = get_headers("GET", test_url)
    print(f"\nHeaders: {headers}")
