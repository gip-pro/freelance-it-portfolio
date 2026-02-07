import yaml
import logging
from datetime import datetime
from typing import Set

from http_client import HttpClient
from parser import (
    parse_category,
    parse_pagination,
    parse_listing,
    parse_owner_profile,
)
from storage import write_row
from geocode import Geocoder
from state import load_state, save_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

REQUIRED_LISTING_SELECTORS = ["title", "price", "address"]

def validate_config(config: dict):
    for site in config["sites"]:
        selectors = site.get("selectors", {})
        listing = selectors.get("listing")
        if not listing:
            raise RuntimeError(f"Missing listing selectors for site {site['name']}")
        for key in REQUIRED_LISTING_SELECTORS:
            if key not in listing:
                raise RuntimeError(f"Missing selector '{key}' in listing for site {site['name']}")

def run():
    with open("scraper/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    validate_config(config)

    processed: Set[str] = set()
    if config["resume"]["enabled"]:
        processed = load_state(config["resume"]["state_file"])

    geocoder = Geocoder(
        cache_file=config["geocoding"]["cache_file"],
        rate_limit_per_minute=config["geocoding"]["rate_limit_per_minute"],
        user_agent=config["geocoding"]["user_agent"],
    )

    processed_batch = 0

    for site in config["sites"]:
        logger.info(f"Start site: {site['name']}")
        client = HttpClient(
            rate_limit_per_minute=site["rate_limit_per_minute"],
            delay_min=site["delay_min_seconds"],
            delay_max=site["delay_max_seconds"],
        )

        total_parsed = 0

        for start_url in site["start_urls"]:
            next_url = start_url
            while next_url:
                logger.info(f"Category page: {next_url}")
                html = client.get(next_url)
                if not html:
                    logger.warning(f"Empty category page: {next_url}")
                    break

                listing_urls = parse_category(
                    html,
                    site["base_url"],
                    site["selectors"]["category_card_links"],
                )

                for url in listing_urls:
                    if url in processed:
                        continue

                    page = client.get(url)
                    if not page:
                        logger.warning(f"Listing unavailable: {url}")
                        continue

                    listing = parse_listing(
                        page,
                        url,
                        site["selectors"]["listing"],
                    )

                    owner_name = listing.get("owner_card_name")
                    phone = listing.get("owner_card_phone")
                    email = listing.get("owner_card_email")
                    contact_source = "listing"

                    if listing.get("owner_profile_url"):
                        owner_page = client.get(site["base_url"] + listing["owner_profile_url"])
                        if owner_page:
                            owner = parse_owner_profile(
                                owner_page,
                                site["selectors"]["owner_profile"],
                            )
                            if owner.get("phone") or owner.get("email"):
                                owner_name = owner.get("owner_name") or owner_name
                                phone = owner.get("phone") or phone
                                email = owner.get("email") or email
                                contact_source = "owner_profile_priority"

                    lat, lon = None, None
                    if config["geocoding"]["enabled"] and listing.get("address"):
                        lat, lon = geocoder.geocode(listing["address"])

                    row = {
                        "source": site["name"],
                        "listing_url": url,
                        "date": datetime.utcnow().isoformat(),
                        "title": listing.get("title"),
                        "price": listing.get("price"),
                        "currency": listing.get("currency"),
                        "address": listing.get("address"),
                        "address_status": listing.get("address_status"),
                        "lat": lat,
                        "lon": lon,
                        "owner_name": owner_name,
                        "phone": phone,
                        "email": email,
                        "contact_source": contact_source,
                        "notes": None,
                    }

                    write_row(
                        config["output"]["csv_path"],
                        row,
                        config["output"]["encoding"],
                    )

                    processed.add(url)
                    processed_batch += 1
                    total_parsed += 1

                    if processed_batch >= config["output"]["batch_state_size"]:
                        save_state(config["resume"]["state_file"], processed)
                        processed_batch = 0

                    if config["test_mode"]["enabled"] and total_parsed >= config["test_mode"]["limit"]:
                        save_state(config["resume"]["state_file"], processed)
                        return

                next_url = parse_pagination(
                    html,
                    site["base_url"],
                    site["selectors"]["pagination_next"],
                )

    if config["resume"]["enabled"]:
        save_state(config["resume"]["state_file"], processed)

if __name__ == "__main__":
    run()