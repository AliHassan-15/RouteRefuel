"""CSV parsing + deduplication (pure logic, unit-testable without Django DB)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from fuel.constants import CANADIAN_PROVINCE_CODES, US_STATE_CODES


@dataclass(frozen=True)
class RawStation:
    opis_id: int
    name: str
    address: str
    city: str
    state: str
    rack_id: str
    price_per_gallon: float


def _name_completeness(name: str) -> tuple[int, int]:
    """Prefer longer, more descriptive names when deduplicating."""
    return (len(name), name.count(" "))


def dedupe_stations(rows: Iterable[RawStation]) -> list[RawStation]:
    """
    Deduplicate by OPIS Truckstop ID.

    Keep the record with the more complete name. If prices differ across
    duplicates for the same ID, keep the lowest listed price (paired with
    that preferred name / address metadata).
    """
    best: dict[int, RawStation] = {}
    for row in rows:
        existing = best.get(row.opis_id)
        if existing is None:
            best[row.opis_id] = row
            continue

        prefer_new_name = _name_completeness(row.name) > _name_completeness(existing.name)
        chosen_name = row.name if prefer_new_name else existing.name
        chosen_address = row.address if prefer_new_name else existing.address
        chosen_city = row.city if prefer_new_name else existing.city
        chosen_state = row.state if prefer_new_name else existing.state
        chosen_rack = row.rack_id if prefer_new_name else existing.rack_id
        chosen_price = min(existing.price_per_gallon, row.price_per_gallon)

        best[row.opis_id] = RawStation(
            opis_id=row.opis_id,
            name=chosen_name,
            address=chosen_address,
            city=chosen_city,
            state=chosen_state,
            rack_id=chosen_rack,
            price_per_gallon=chosen_price,
        )
    return sorted(best.values(), key=lambda s: s.opis_id)


def parse_fuel_csv(path: Path) -> tuple[list[RawStation], dict[str, int]]:
    """
    Parse the assessment CSV.

    Returns (usa_deduped_stations, stats).
    Canadian province rows are counted and skipped.
    """
    stats = {
        "rows_read": 0,
        "canadian_skipped": 0,
        "non_us_skipped": 0,
        "parse_errors": 0,
        "duplicates_collapsed": 0,
    }
    raw: list[RawStation] = []

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            stats["rows_read"] += 1
            try:
                state = (row.get("State") or "").strip().upper()
                if state in CANADIAN_PROVINCE_CODES:
                    stats["canadian_skipped"] += 1
                    continue
                if state not in US_STATE_CODES:
                    stats["non_us_skipped"] += 1
                    continue

                raw.append(
                    RawStation(
                        opis_id=int(str(row["OPIS Truckstop ID"]).strip()),
                        name=(row.get("Truckstop Name") or "").strip(),
                        address=(row.get("Address") or "").strip(),
                        city=(row.get("City") or "").strip(),
                        state=state,
                        rack_id=str(row.get("Rack ID") or "").strip(),
                        price_per_gallon=float(str(row["Retail Price"]).strip()),
                    )
                )
            except (KeyError, TypeError, ValueError):
                stats["parse_errors"] += 1

    before = len(raw)
    deduped = dedupe_stations(raw)
    stats["duplicates_collapsed"] = before - len(deduped)
    stats["usa_unique_stations"] = len(deduped)
    return deduped, stats
