#!/usr/bin/env python3
"""
Letterboxd Movie Fetcher
Fetches movies from a Letterboxd profile using RSS feeds and web scraping.
"""

import xml.etree.ElementTree as ET
import urllib.request
import re
from dataclasses import dataclass
from typing import Optional
import html


@dataclass
class Film:
    title: str
    year: Optional[str] = None
    rating: Optional[str] = None
    watch_date: Optional[str] = None
    link: Optional[str] = None
    rewatch: bool = False


def parse_films_page(page_html: str) -> list[Film]:
    """Parse films from Letterboxd HTML using regex."""
    films = []

    # Find all film links and titles
    # Pattern: data-target-link="/film/slug/" followed by img alt="Title"
    pattern = r'data-target-link="(/film/[^"]+/)"[^>]*>.*?<img[^>]*alt="([^"]+)"'
    matches = re.findall(pattern, page_html, re.DOTALL)

    for link, title in matches:
        # Decode HTML entities
        title = html.unescape(title)
        films.append(Film(
            title=title,
            link=f"https://letterboxd.com{link}"
        ))

    return films


def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8')


def fetch_from_rss(username: str) -> list[Film]:
    """Fetch recently watched films from RSS feed."""
    url = f"https://letterboxd.com/{username}/rss/"
    content = fetch_url(url)

    root = ET.fromstring(content)
    films = []

    for item in root.findall('.//item'):
        title_elem = item.find('title')
        link_elem = item.find('link')
        description = item.find('description')

        if title_elem is None:
            continue

        full_title = title_elem.text or ""

        # Parse title and year (format: "Title, Year")
        match = re.match(r'^(.+),\s*(\d{4})$', full_title)
        if match:
            title = match.group(1)
            year = match.group(2)
        else:
            title = full_title
            year = None

        # Parse rating from description
        rating = None
        rewatch = False
        watch_date = None

        if description is not None and description.text:
            desc = description.text

            # Extract star rating
            rating_match = re.search(r'★+[½]?', desc)
            if rating_match:
                rating = rating_match.group()

            # Check for rewatch
            rewatch = 'Rewatched' in desc

            # Extract watch date
            date_match = re.search(r'Watched on\s+\w+\s+(\w+\s+\d+,\s+\d{4})', desc)
            if date_match:
                watch_date = date_match.group(1)

        films.append(Film(
            title=title,
            year=year,
            rating=rating,
            link=link_elem.text if link_elem is not None else None,
            watch_date=watch_date,
            rewatch=rewatch
        ))

    return films


def fetch_all_films(username: str) -> list[Film]:
    """Fetch all watched films by scraping the films page."""
    films = []
    page = 1

    while True:
        url = f"https://letterboxd.com/{username}/films/page/{page}/"
        try:
            content = fetch_url(url)
        except Exception:
            break

        page_films = parse_films_page(content)

        if not page_films:
            break

        films.extend(page_films)
        page += 1

        # Safety limit
        if page > 50:
            break

    return films


def fetch_watchlist(username: str) -> list[Film]:
    """Fetch films from user's watchlist."""
    films = []
    page = 1

    while True:
        url = f"https://letterboxd.com/{username}/watchlist/page/{page}/"
        try:
            content = fetch_url(url)
        except Exception:
            break

        page_films = parse_films_page(content)

        if not page_films:
            break

        films.extend(page_films)
        page += 1

        if page > 20:
            break

    return films


def main():
    username = "szymonindy"

    print(f"Fetching Letterboxd data for: {username}")
    print("=" * 50)

    # Fetch from RSS (recent activity with ratings)
    print("\n📽  Recent Activity (from RSS):")
    print("-" * 40)
    rss_films = fetch_from_rss(username)
    for film in rss_films[:10]:
        rating_str = f" {film.rating}" if film.rating else ""
        rewatch_str = " (rewatch)" if film.rewatch else ""
        year_str = f" ({film.year})" if film.year else ""
        print(f"  • {film.title}{year_str}{rating_str}{rewatch_str}")

    if len(rss_films) > 10:
        print(f"  ... and {len(rss_films) - 10} more")

    # Fetch all watched films
    print("\n🎬  All Watched Films:")
    print("-" * 40)
    all_films = fetch_all_films(username)
    print(f"  Total: {len(all_films)} films")
    for film in all_films[:5]:
        year_str = f" ({film.year})" if film.year else ""
        print(f"  • {film.title}{year_str}")
    if len(all_films) > 5:
        print(f"  ... and {len(all_films) - 5} more")

    # Fetch watchlist
    print("\n📋  Watchlist:")
    print("-" * 40)
    watchlist = fetch_watchlist(username)
    print(f"  Total: {len(watchlist)} films")
    for film in watchlist[:5]:
        year_str = f" ({film.year})" if film.year else ""
        print(f"  • {film.title}{year_str}")
    if len(watchlist) > 5:
        print(f"  ... and {len(watchlist) - 5} more")


if __name__ == "__main__":
    main()
