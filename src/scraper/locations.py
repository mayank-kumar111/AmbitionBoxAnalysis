"""Location presets used by the incremental collection pipeline."""

# Original project locations.
CORE_LOCATIONS = [
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

# Additional discovery locations. They are opt-in through the scraper CLI so
# the baseline ten-location dataset is never unexpectedly overwritten.
EXTENDED_LOCATIONS = CORE_LOCATIONS + [
    "delhi",
    "kolkata",
    "chandigarh",
    "kochi",
    "coimbatore",
    "lucknow",
    "nagpur",
    "surat",
    "vadodara",
    "bhubaneswar",
]
