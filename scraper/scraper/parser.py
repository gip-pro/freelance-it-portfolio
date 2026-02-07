from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def parse_category(html: str, base_url: str, selector: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    urls = []
    for a in soup.select(selector):
        href = a.get("href")
        if href:
            urls.append(urljoin(base_url, href))
    return list(set(urls))

def parse_pagination(html: str, base_url: str, selector: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    link = soup.select_one(selector)
    if link and link.get("href"):
        return urljoin(base_url, link.get("href"))
    return None

def extract_address(soup: BeautifulSoup, selectors: List[str]) -> Tuple[Optional[str], str]:
    for sel in selectors:
        el = soup.select_one(sel)
        if not el:
            continue
        text = el.get_text(strip=True)
        if not text:
            continue
        has_number = bool(re.search(r"\d", text))
        if has_number:
            return text, "full"
        return text, "partial"
    return None, "not_found"

def extract_currency(price: Optional[str]) -> Optional[str]:
    if not price:
        return None
    if "€" in price:
        return "EUR"
    if "$" in price:
        return "USD"
    if "£" in price:
        return "GBP"
    match = re.search(r"\b[A-Z]{3}\b", price)
    if match:
        return match.group(0)
    return None

def parse_listing(html: str, url: str, selectors: Dict) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    def txt(sel):
        el = soup.select_one(sel)
        return el.get_text(strip=True) if el else None

    address, address_status = extract_address(soup, selectors["address"])
    price = txt(selectors["price"])

    data = {
        "listing_url": url,
        "title": txt(selectors["title"]),
        "price": price,
        "currency": extract_currency(price),
        "address": address,
        "address_status": address_status,
        "owner_profile_url": None,
        "owner_card_name": txt(selectors.get("owner_name")) if selectors.get("owner_name") else None,
        "owner_card_phone": txt(selectors.get("owner_phone")) if selectors.get("owner_phone") else None,
        "owner_card_email": txt(selectors.get("owner_email")) if selectors.get("owner_email") else None,
    }

    owner_link = soup.select_one(selectors.get("owner_profile"))
    if owner_link and owner_link.get("href"):
        data["owner_profile_url"] = owner_link.get("href")

    return data

def parse_owner_profile(html: str, selectors: Dict) -> Dict:
    soup = BeautifulSoup(html, "lxml")

    def txt(sel):
        el = soup.select_one(sel)
        return el.get_text(strip=True) if el else None

    return {
        "owner_name": txt(selectors.get("name")),
        "phone": txt(selectors.get("phone")),
        "email": txt(selectors.get("email")),
    }