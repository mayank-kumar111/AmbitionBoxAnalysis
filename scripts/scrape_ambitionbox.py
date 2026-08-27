"""CLI entry point for AmbitionBox collection."""

import logging

from src.scraper.ambitionbox_scraper import AmbitionBoxScraper


LOCATIONS = [
    "jaipur",
    "bangalore",
    "hyderabad",
    "pune",
    "chennai",
    "mumbai",
    "noida",
    "gurugram",
    "ahmedabad",
    "indore",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    scraper = AmbitionBoxScraper()
    scraper.scrape_locations(LOCATIONS, "csv_files")
