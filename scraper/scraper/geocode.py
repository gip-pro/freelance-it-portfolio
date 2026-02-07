import json
import os
import logging
from typing import Optional, Tuple
import requests
import time

logger = logging.getLogger(__name__)

class Geocoder:
    def __init__(self, cache_file: str, rate_limit_per_minute: int, user_agent: str):
        self.cache_file = cache_file
        self.rate_limit = rate_limit_per_minute
        self.user_agent = user_agent
        self.cache = {}
        self.last_request_ts = None
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                self.cache = json.load(f)

    def _respect_rate_limit(self):
        if self.last_request_ts is None:
            return
        min_interval = 60.0 / max(1, self.rate_limit)
        elapsed = time.time() - self.last_request_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def geocode(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        if not address:
            return None, None
        if address in self.cache:
            return self.cache[address]

        self._respect_rate_limit()
        try:
            resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": address, "format": "json", "limit": 1},
                headers={"User-Agent": self.user_agent},
                timeout=20,
            )
            self.last_request_ts = time.time()
            resp.raise_for_status()
            data = resp.json()
            if not data:
                self.cache[address] = (None, None)
                return None, None
            lat = float(data[0].get("lat"))
            lon = float(data[0].get("lon"))
            self.cache[address] = (lat, lon)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f)
            return lat, lon
        except Exception as e:
            logger.error(f"Geocoding failed for '{address}': {e}")
            return None, None