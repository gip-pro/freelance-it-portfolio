# Rental Listings Scraper

## Purpose
This project collects short-term rental listings from publicly available websites and saves them into a CSV file.

## Key Notes and Limitations
- robots.txt is NOT checked. The scraper assumes you manually ensure compliance.
- Only publicly accessible pages are processed.
- No logins, no private data, no bypassing of protections.
- Geocoding uses the Nominatim (OpenStreetMap) API:
  - Strict request rate limits apply.
  - A local cache is used to reduce repeated requests.
  - Coordinates may be missing or approximate.

## Features
- Site-specific CSS selectors configured via config.yaml
- Category and pagination crawling
- Listing card parsing
- Optional owner profile parsing
- Public contact extraction (phone and email when available)
- Address extraction with status:
  - full — street address with house number
  - partial — city or district without street or house
  - not_found — no address detected
- Currency detection from price (symbol or ISO code when present)
- CSV output with stable column order
- Resume support (state saved in batches)
- Test mode with record limit

## Requirements
- Python 3.10 or newer

## Installation
pip install requests pyyaml beautifulsoup4 lxml

## Configuration
Edit scraper/config.yaml:
- sites: base_url, start_urls, CSS selectors
- Rate limits and delays (anti-blocking)
- CSV output path and encoding
- Resume and test mode options

## Running
python scraper/main.py

## Output
- CSV file encoded in UTF-8
- One row per listing
- Duplicate listings are not written on repeated runs

## Disclaimer
This tool is intended for educational and analytical purposes.
You are responsible for complying with the terms of service of the target websites.