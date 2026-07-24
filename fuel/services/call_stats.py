"""Request-scoped counters for external HTTP calls (demo / observability)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExternalCallStats:
    geocode_network: int = 0
    geocode_cache_hits: int = 0
    routing_network: int = 0
    routing_cache_hits: int = 0

    @property
    def total_network(self) -> int:
        return self.geocode_network + self.routing_network

    def as_dict(self) -> dict:
        return {
            "geocode": self.geocode_network,
            "routing": self.routing_network,
            "total": self.total_network,
            "geocode_cache_hits": self.geocode_cache_hits,
            "routing_cache_hits": self.routing_cache_hits,
            "per_station": 0,
        }
