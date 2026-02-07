import time
import random
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

class HttpClient:
    def __init__(self, rate_limit_per_minute: int, delay_min: int, delay_max: int):
        self.session = requests.Session()
        self.rate_limit = rate_limit_per_minute
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.last_request_ts: Optional[float] = None

    def _respect_rate_limit(self):
        if self.last_request_ts is None:
            return
        min_interval = 60.0 / max(1, self.rate_limit)
        elapsed = time.time() - self.last_request_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    def get(self, url: str, headers: Optional[dict] = None) -> Optional[str]:
        self._respect_rate_limit()
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
        try:
            resp = self.session.get(url, headers=headers, timeout=30)
            self.last_request_ts = time.time()
            if resp.status_code in (403, 429):
                logger.warning(f"Blocked with status {resp.status_code} for {url}")
                return None
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None