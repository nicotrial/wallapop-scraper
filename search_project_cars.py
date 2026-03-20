#!/usr/bin/env python3
"""
Wallapop Project Car Search Tool

CLI tool for searching project cars on Wallapop marketplace.
"""

import argparse
import json
import csv
import sys
from typing import Optional
from wallapop_client import WallapopClient, format_item, WallapopAPIError


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Search for project cars on Wallapop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --keywords "bmw e36" --max-price 3000
  %(prog)s --keywords "coche proyecto" --location 40.4168 -3.7038 --radius 50
  %(prog)s --keywords "seat 600" --min-price 500 --max-price 5000 --output results.json
        """
    )

    parser.add_argument(
        '--keywords', '-k',
        type=str,
        default='coche proyecto',
        help='Search keywords (default: "coche proyecto")'
    )

    parser.add_argument(
        '--min-price',
        type=int,
        help='Minimum price in EUR'
    )

    parser.add_argument(
        '--max-price',
        type=int,
        help='Maximum price in EUR'
    )

    parser.add_argument(
        '--latitude', '--lat',
        type=float,
        help='Location latitude (e.g., 40.4168 for Madrid)'
    )

    parser.add_argument(
        '--longitude', '--lon',
        type=float,
        help='Location longitude (e.g., -3.7038 for Madrid)'
    )

    parser.add_argument(
        '--radius', '-r',
        type=int,
        default=50,
        help='Search radius in km (default: 50)'
    )

    parser.add_argument(
        '--order-by', '-o',
        type=str,
        default='newest',
        choices=['newest', 'price_low', 'price_high', 'closest'],
        help='Sort order (default: newest)'
    )

    parser.add_argument(
        '--time-filter', '-t',
        type=str,
        choices=['today', 'last_week'],
        help='Filter by listing time'
    )

    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=20,
        help='Maximum number of results to display (default: 20)'
    )

    parser.add_argument(
        '--output', '-f',
        type=str,
        help='Output file (JSON or CSV based on extension)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between requests in seconds (default: 2.0)'
    )

    parser.add_argument(
        '--raw',
        action='store_true',
        help='Output raw JSON response'
    )

    return parser.parse_args()


def print_results(items: list, limit: int = 20):
    """
    Print search results in a formatted way.

    Args:
        items: List of formatted items
        limit: Maximum number of items to display
    """
    if not items:
        print("No results found.")
        return

    print(f"\n{'=' * 80}")
    print(f"Found {len(items)} results (showing first {min(limit, len(items))})")
    print(f"{'=' * 80}\n")

    for i, item in enumerate(items[:limit], 1):
        print(f"[{i}] {item.get('title', 'N/A')}")
        print(f"    Price: {item.get('price', 'N/A')} {item.get('currency', 'EUR')}")
        print(f"    Location: {item.get('city', 'N/A')}")
        print(f"    Seller: {item.get('seller', 'N/A')}")

        if item.get('description'):
            desc = item['description'][:150]
            if len(item['description']) > 150:
                desc += '...'
            print(f"    Description: {desc}")

        if item.get('url'):
            print(f"    URL: {item['url']}")

        if item.get('image_url'):
            print(f"    Image: {item['image_url']}")

        print()


def save_to_json(items: list, filename: str):
    """Save results to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(items)} results to {filename}")


def save_to_csv(items: list, filename: str):
    """Save results to a CSV file."""
    if not items:
        print("No results to save.")
        return

    fieldnames = ['id', 'title', 'price', 'currency', 'city', 'postal_code',
                  'seller', 'url', 'image_url', 'description']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)

    print(f"\nSaved {len(items)} results to {filename}")


def main():
    """Main entry point."""
    args = parse_args()

    # Create client
    client = WallapopClient(delay=args.delay)

    # Build location parameters
    latitude = args.latitude
    longitude = args.longitude
    distance_in_km = args.radius if (latitude and longitude) else None

    print(f"Searching for: '{args.keywords}'")
    if args.min_price:
        print(f"  Min price: {args.min_price} EUR")
    if args.max_price:
        print(f"  Max price: {args.max_price} EUR")
    if latitude and longitude:
        print(f"  Location: {latitude}, {longitude} (radius: {distance_in_km}km)")
    print(f"  Order by: {args.order_by}")
    if args.time_filter:
        print(f"  Time filter: {args.time_filter}")
    print()

    try:
        # Make the search request
        results = client.search_cars(
            keywords=args.keywords,
            min_price=args.min_price,
            max_price=args.max_price,
            latitude=latitude,
            longitude=longitude,
            distance_in_km=distance_in_km,
            order_by=args.order_by
        )

        # Handle raw output
        if args.raw:
            print(json.dumps(results, indent=2, ensure_ascii=False))
            return

        # Extract and format items
        raw_items = results.get('search_objects', [])
        formatted_items = [format_item(item) for item in raw_items]

        # Print results
        print_results(formatted_items, args.limit)

        # Save to file if specified
        if args.output:
            if args.output.endswith('.json'):
                save_to_json(formatted_items, args.output)
            elif args.output.endswith('.csv'):
                save_to_csv(formatted_items, args.output)
            else:
                # Default to JSON
                save_to_json(formatted_items, args.output + '.json')

    except WallapopAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSearch cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
