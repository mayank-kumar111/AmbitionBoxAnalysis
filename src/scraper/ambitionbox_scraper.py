"""Reusable, defensive AmbitionBox company-list scraper.

The scraper is intentionally isolated from notebooks so collection can be
re-run without coupling it to cleaning, analysis, or the Flask application.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import ScraperConfig

LOGGER = logging.getLogger(__name__)

CARD_CLASS = "companyCardWrapper__metaInformation"
RATING_CLASS = "companyCardWrapper__companyRatingValue"
DETAILS_CLASS = "companyCardWrapper__interLinking"


class AmbitionBoxScraper:
    """Collect company cards for one or more locations."""

    def __init__(self, config: ScraperConfig | None = None) -> None:
        self.config = config or ScraperConfig()
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=self.config.max_retries,
            connect=self.config.max_retries,
            read=self.config.max_retries,
            status=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update(self.config.headers)
        return session

    def fetch_page(self, location: str, page: int) -> str:
        """Fetch one listing page and raise on an unsuccessful response."""
        response = self.session.get(
            self.config.base_url,
            params={"sortBy": "popular", "locations": location, "page": page},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.text

    @staticmethod
    def parse_page(html: str) -> list[dict[str, str | None]]:
        """Extract company name, rating, and normalized raw detail text from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        rows: list[dict[str, str | None]] = []

        for card in soup.find_all("div", class_=CARD_CLASS):
            name_node = card.find("h2")
            rating_node = card.find("span", class_=RATING_CLASS)
            details_node = card.find("span", class_=DETAILS_CLASS)

            details = None
            if details_node:
                parts = details_node.get_text("|", strip=True).split("|")
                details = ", ".join(part.strip() for part in parts if part.strip())

            rows.append(
                {
                    "company_name": name_node.get_text(strip=True) if name_node else None,
                    "company_rating": rating_node.get_text(strip=True) if rating_node else None,
                    "other_data": details,
                }
            )

        return rows

    def scrape_location(self, location: str) -> pd.DataFrame:
        """Scrape all configured pages for a location."""
        records: list[dict[str, str | None]] = []

        for page in range(1, self.config.pages + 1):
            try:
                html = self.fetch_page(location, page)
                page_records = self.parse_page(html)
            except requests.RequestException as exc:
                LOGGER.error("%s page %s failed: %s", location, page, exc)
                continue

            if not page_records:
                LOGGER.info(
                    "%s page %s returned no company cards; stopping",
                    location,
                    page,
                )
                break

            records.extend(page_records)
            LOGGER.info("%s page %s: %s companies", location, page, len(page_records))
            time.sleep(self.config.delay)

        return pd.DataFrame(records, columns=["company_name", "company_rating", "other_data"])

    def scrape_locations(
        self, locations: list[str], output_dir: str | Path
    ) -> dict[str, pd.DataFrame]:
        """Scrape locations sequentially and persist one CSV per location."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        results: dict[str, pd.DataFrame] = {}

        for location in locations:
            LOGGER.info("Starting location: %s", location)
            df = self.scrape_location(location)
            results[location] = df
            df.to_csv(output_path / f"{location}.csv", index=False)
            LOGGER.info("Saved %s rows for %s", len(df), location)

        return results
