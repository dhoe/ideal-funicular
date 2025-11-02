#!/usr/bin/env python3
"""
Semantic Scholar Paper Search Script
Searches for papers on emotional regulation in essential tremor
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Semantic Scholar API configuration
SEMANTIC_SCHOLAR_API = 'https://api.semanticscholar.org/graph/v1/paper/search'


def search_papers(query: str, limit: int = 100) -> Optional[Dict]:
    """
    Search for papers on Semantic Scholar

    Args:
        query: The search query
        limit: Maximum number of results (default: 100, max: 100)

    Returns:
        Search results dictionary or None on error
    """
    print(f'Searching Semantic Scholar for: "{query}"\n')

    # Setup proxy if configured
    proxies = {}
    proxy_url = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
    if proxy_url:
        proxies = {'https': proxy_url, 'http': proxy_url}
        print(f'Using proxy: {proxy_url}\n')

    params = {
        'query': query,
        'limit': limit,
        'fields': 'paperId,title,abstract,year,authors,publicationDate,citationCount,url,venue,publicationTypes,isOpenAccess,openAccessPdf'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }

    try:
        response = requests.get(
            SEMANTIC_SCHOLAR_API,
            params=params,
            headers=headers,
            proxies=proxies if proxies else None,
            timeout=15
        )

        if response.status_code == 403:
            print('❌ Access denied (403). Trying without proxy...\n')

            # Retry without proxy
            try:
                retry_response = requests.get(
                    SEMANTIC_SCHOLAR_API,
                    params=params,
                    headers=headers,
                    timeout=15
                )
                if retry_response.status_code == 200:
                    return retry_response.json()
            except Exception as e:
                print(f'Retry without proxy also failed: {e}')

            raise Exception(
                'Access denied. The Semantic Scholar API may be blocking requests from this network. Try:\n'
                '  1. Running from a different network\n'
                '  2. Using an API key (see https://www.semanticscholar.org/product/api)\n'
                '  3. Accessing the website directly: https://www.semanticscholar.org/'
            )

        if response.status_code == 429:
            raise Exception('Rate limit exceeded. Please wait a few minutes and try again.')

        if response.status_code != 200:
            raise Exception(f'API returned status {response.status_code}: {response.reason}')

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f'Network error: {e}')
        raise
    except Exception as e:
        print(f'Error: {e}')
        raise


def display_results(results: Dict) -> None:
    """
    Format and display search results

    Args:
        results: Search results from Semantic Scholar
    """
    if not results.get('data') or len(results['data']) == 0:
        print('No papers found.')
        return

    print(f"Found {results.get('total', 0)} total papers (showing {len(results['data'])})\n")
    print('=' * 80)

    for index, paper in enumerate(results['data'], 1):
        print(f"\n{index}. {paper.get('title', 'N/A')}")
        print('-' * 80)
        print(f"Year: {paper.get('year', 'N/A')}")

        authors = paper.get('authors', [])
        if authors:
            author_names = ', '.join(author.get('name', 'Unknown') for author in authors)
            print(f"Authors: {author_names}")
        else:
            print("Authors: N/A")

        print(f"Citations: {paper.get('citationCount', 0)}")
        print(f"Venue: {paper.get('venue', 'N/A')}")
        print(f"Open Access: {'Yes' if paper.get('isOpenAccess') else 'No'}")

        open_access_pdf = paper.get('openAccessPdf')
        if open_access_pdf and open_access_pdf.get('url'):
            print(f"PDF: {open_access_pdf['url']}")

        print(f"URL: {paper.get('url', 'N/A')}")

        abstract = paper.get('abstract', '')
        if abstract:
            abstract_preview = abstract[:200]
            if len(abstract) > 200:
                abstract_preview += '...'
            print(f"\nAbstract: {abstract_preview}")

    print('\n' + '=' * 80)


def save_results(results: Dict, filename: str) -> None:
    """
    Save results to a JSON file

    Args:
        results: Search results
        filename: Output filename
    """
    output_path = f'./{filename}'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f'\nResults saved to: {output_path}')


def print_statistics(results: Dict) -> None:
    """
    Print summary statistics about the results

    Args:
        results: Search results
    """
    print('\n📊 Summary Statistics:')
    print(f"Total papers found: {results.get('total', 0)}")

    data = results.get('data', [])
    print(f"Papers retrieved: {len(data)}")

    if data:
        open_access_count = sum(1 for p in data if p.get('isOpenAccess'))
        open_access_pct = (open_access_count / len(data)) * 100
        print(f"Open access papers: {open_access_count} ({open_access_pct:.1f}%)")

        citations = [p.get('citationCount', 0) for p in data]
        avg_citations = sum(citations) / len(citations)
        print(f"Average citations: {avg_citations:.1f}")

        years = [p.get('year') for p in data if p.get('year')]
        if years:
            print(f"Year range: {min(years)} - {max(years)}")


def main():
    """Main function"""
    query = 'emotional regulation essential tremor'
    limit = 50  # Get up to 50 papers

    print('🔍 Semantic Scholar Paper Search')
    print('=' * 80)
    print(f'Query: {query}')
    print(f'Limit: {limit} papers\n')

    try:
        results = search_papers(query, limit)

        if results:
            display_results(results)

            # Save results to file
            timestamp = datetime.now().strftime('%Y-%m-%d')
            filename = f'semantic-scholar-results-{timestamp}.json'
            save_results(results, filename)

            # Print statistics
            print_statistics(results)
        else:
            print('No results returned.')
            sys.exit(1)

    except Exception as e:
        print(f'\n❌ Failed to complete search: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
