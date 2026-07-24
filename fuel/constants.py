"""Vehicle and algorithm constants — never use magic numbers in business logic."""

# Vehicle assumptions from the assignment
MAX_RANGE_MILES = 500
MPG = 10
TANK_CAPACITY_GALLONS = MAX_RANGE_MILES / MPG  # 50.0

# Keep a reserve so we never plan to arrive on empty.
RANGE_RESERVE_MILES = 30
USABLE_RANGE_MILES = MAX_RANGE_MILES - RANGE_RESERVE_MILES  # 470

# A station must snap within this distance of the route polyline to be eligible.
# 25 mi is intentional: stations are geocoded at City+State precision (exit-style
# addresses rarely geocode cleanly), so a tighter corridor would drop valid stops.
ROUTE_CORRIDOR_MILES = 25.0

# Assumed dwell time while fueling (used only for ETAs).
FUEL_STOP_DWELL_SECONDS = 12 * 60

# Soft safety cap on stop count for pathological cases.
MAX_FUEL_STOPS = 40

# US state codes accepted for this USA-only product.
US_STATE_CODES = frozenset(
    {
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    }
)

# Canadian provinces that appear in the CSV State column — filtered on ingest.
CANADIAN_PROVINCE_CODES = frozenset(
    {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"}
)
