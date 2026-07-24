"""Fast USA place suggestions from the offline cities index (no per-keystroke HTTP)."""

from __future__ import annotations

import csv
import re
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.conf import settings

# Expand common US place abbreviations so "St. Louis" matches "Saint Louis".
# Compass letters only expand with a trailing period ("N. Something"), never lone n/s/e/w.
_ABBREV_EXPAND = (
    (re.compile(r"\bst\.?\b"), "saint"),
    (re.compile(r"\bft\.?\b"), "fort"),
    (re.compile(r"\bmt\.?\b"), "mount"),
    (re.compile(r"\bmtn\.?\b"), "mountain"),
    (re.compile(r"\bpt\.?\b"), "point"),
    (re.compile(r"\bn\.\b"), "north"),
    (re.compile(r"\bs\.\b"), "south"),
    (re.compile(r"\be\.\b"), "east"),
    (re.compile(r"\bw\.\b"), "west"),
)


def _expand_abbreviations(text: str) -> str:
    # Expand while periods are still present ("St.", "N."), then strip punctuation.
    out = text.strip().lower()
    for pattern, repl in _ABBREV_EXPAND:
        out = pattern.sub(repl, out)
    out = out.replace(".", " ")
    out = re.sub(r"[^a-z0-9\s,]", " ", out)
    return re.sub(r"\s+", " ", out).strip()


def _tokens(text: str) -> list[str]:
    return [t for t in _expand_abbreviations(text).replace(",", " ").split() if t]


def _display_city(city: str) -> str:
    """Prefer familiar St./Ft./Mt. spellings in the UI."""
    out = re.sub(r"\bSaint\b", "St.", city)
    out = re.sub(r"\bFort\b", "Ft.", out)
    out = re.sub(r"\bMount\b", "Mt.", out)
    return out


# Prefer well-known metros in typeahead (offline popularity bias).
_MAJOR_CITIES = frozenset(
    {
        ("new york", "NY"),
        ("los angeles", "CA"),
        ("chicago", "IL"),
        ("houston", "TX"),
        ("phoenix", "AZ"),
        ("philadelphia", "PA"),
        ("san antonio", "TX"),
        ("san diego", "CA"),
        ("dallas", "TX"),
        ("san jose", "CA"),
        ("austin", "TX"),
        ("jacksonville", "FL"),
        ("fort worth", "TX"),
        ("columbus", "OH"),
        ("charlotte", "NC"),
        ("san francisco", "CA"),
        ("indianapolis", "IN"),
        ("seattle", "WA"),
        ("denver", "CO"),
        ("washington", "DC"),
        ("boston", "MA"),
        ("nashville", "TN"),
        ("detroit", "MI"),
        ("oklahoma city", "OK"),
        ("portland", "OR"),
        ("las vegas", "NV"),
        ("memphis", "TN"),
        ("louisville", "KY"),
        ("baltimore", "MD"),
        ("milwaukee", "WI"),
        ("albuquerque", "NM"),
        ("tucson", "AZ"),
        ("fresno", "CA"),
        ("sacramento", "CA"),
        ("atlanta", "GA"),
        ("miami", "FL"),
        ("minneapolis", "MN"),
        ("cleveland", "OH"),
        ("tampa", "FL"),
        ("orlando", "FL"),
        ("saint louis", "MO"),
        ("east saint louis", "IL"),
        ("pittsburgh", "PA"),
        ("cincinnati", "OH"),
        ("kansas city", "MO"),
        ("raleigh", "NC"),
        ("salt lake city", "UT"),
        ("richmond", "VA"),
        ("buffalo", "NY"),
        ("new orleans", "LA"),
    }
)


@dataclass(frozen=True, slots=True)
class PlaceSuggestion:
    label: str
    city: str
    state: str
    latitude: float
    longitude: float


class PlaceSuggestIndex:
    """In-memory search over USA cities for autocomplete."""

    def __init__(self) -> None:
        # (search_name, state, city_display, label, lat, lon)
        self._entries: list[tuple[str, str, str, str, float, float]] = []

    @classmethod
    def from_csv(cls, path: Path) -> "PlaceSuggestIndex":
        instance = cls()
        if not path.exists():
            return instance

        seen: set[tuple[str, str]] = set()
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                city = (row.get("city") or "").strip()
                state = (row.get("state") or "").strip().upper()
                if not city or not state:
                    continue
                search_name = _expand_abbreviations(city)
                key = (search_name, state)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    lat = float(row["latitude"])
                    lon = float(row["longitude"])
                except (KeyError, TypeError, ValueError):
                    continue
                display_city = _display_city(city)
                label = f"{display_city}, {state}"
                instance._entries.append(
                    (search_name, state, display_city, label, lat, lon)
                )

        instance._entries.sort(key=lambda e: (e[0], e[1]))
        return instance

    def suggest(self, query: str, *, limit: int = 12) -> list[PlaceSuggestion]:
        raw = query.strip()
        if len(raw) < 1:
            return []

        limit = max(1, min(int(limit), 20))
        q = _expand_abbreviations(raw)

        q_city = q
        q_state = ""
        if "," in q:
            left, right = q.split(",", 1)
            q_city = left.strip()
            q_state = right.strip().upper().replace(" ", "")
        else:
            parts = q.rsplit(" ", 1)
            if len(parts) == 2 and len(parts[1]) == 2 and parts[1].isalpha():
                q_city = parts[0].strip()
                q_state = parts[1].upper()

        q_tokens = _tokens(q_city)
        if not q_tokens and not q_state:
            return []

        joined_q = " ".join(q_tokens)
        scored: list[tuple[tuple, PlaceSuggestion]] = []

        for search_name, state, city, label, lat, lon in self._entries:
            if q_state and not state.startswith(q_state):
                continue

            if q_tokens:
                city_tokens = search_name.split()
                if self._tokens_match(q_tokens, city_tokens):
                    if search_name == joined_q:
                        match_tier = 0  # exact city name
                    elif search_name.startswith(joined_q + " ") or search_name.startswith(
                        joined_q
                    ):
                        match_tier = 1  # prefix of full name
                    else:
                        match_tier = 2  # ordered token prefixes (e.g. louis in saint louis)
                elif search_name.startswith(joined_q) or joined_q in search_name:
                    match_tier = 3 if search_name.startswith(joined_q) else 4
                else:
                    continue
            else:
                match_tier = 1

            is_major = (search_name, state) in _MAJOR_CITIES
            # Prefer exact-length city names over longer compounds (Louis vs Louisville).
            length_penalty = abs(len(search_name) - len(joined_q)) if q_tokens else len(city)
            suggestion = PlaceSuggestion(label, city, state, lat, lon)
            scored.append(
                (
                    (
                        match_tier,
                        0 if is_major else 1,
                        length_penalty,
                        len(city),
                        label,
                    ),
                    suggestion,
                )
            )

        scored.sort(key=lambda item: item[0])
        out: list[PlaceSuggestion] = []
        seen_labels: set[str] = set()
        for _, suggestion in scored:
            if suggestion.label in seen_labels:
                continue
            seen_labels.add(suggestion.label)
            out.append(suggestion)
            if len(out) >= limit:
                break
        return out

    @staticmethod
    def _tokens_match(query_tokens: list[str], city_tokens: list[str]) -> bool:
        """True if each query token matches a city token in order (prefix allowed)."""
        if not query_tokens:
            return True
        i = 0
        for qt in query_tokens:
            matched = False
            while i < len(city_tokens):
                ct = city_tokens[i]
                i += 1
                if ct.startswith(qt) or qt.startswith(ct):
                    matched = True
                    break
            if not matched:
                return False
        return True


_lock = threading.Lock()
_index: PlaceSuggestIndex | None = None


def get_place_suggest_index() -> PlaceSuggestIndex:
    global _index
    if _index is not None:
        return _index
    with _lock:
        if _index is not None:
            return _index
        path = Path(settings.US_CITIES_CACHE_PATH)
        if not path.exists():
            from fuel.services.city_geocoder import CityCoordinateIndex

            CityCoordinateIndex.load_or_download(path)
        _index = PlaceSuggestIndex.from_csv(path)
        return _index


def reset_place_suggest_cache() -> None:
    """Test helper."""
    global _index
    with _lock:
        _index = None
    suggest_places.cache_clear()


@lru_cache(maxsize=512)
def suggest_places(query: str, limit: int = 12) -> tuple[PlaceSuggestion, ...]:
    """Cached suggestions for identical queries within the process."""
    return tuple(get_place_suggest_index().suggest(query, limit=limit))
