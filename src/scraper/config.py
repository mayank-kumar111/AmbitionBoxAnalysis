"""Configuration for the AmbitionBox scraper."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ScraperConfig:
    base_url: str = "https://www.ambitionbox.com/list-of-companies"
    pages: int = 500
    timeout: float = float(os.getenv("SCRAPER_TIMEOUT", "20"))
    delay: float = float(os.getenv("SCRAPER_DELAY", "1"))
    max_retries: int = 3
    backoff_factor: float = 1.5

    @property
    def headers(self) -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
