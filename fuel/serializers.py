from __future__ import annotations

from datetime import datetime

from rest_framework import serializers


class RoutePlanRequestSerializer(serializers.Serializer):
    start = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
        help_text='USA start location, e.g. "Chicago, IL" or a full address.',
    )
    finish = serializers.CharField(
        max_length=255,
        trim_whitespace=True,
        help_text='USA finish location, e.g. "Dallas, TX".',
    )
    depart_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Optional ISO-8601 departure time used for ETAs (UTC).",
    )

    def validate_start(self, value: str) -> str:
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Start location is too short.")
        return value.strip()

    def validate_finish(self, value: str) -> str:
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Finish location is too short.")
        return value.strip()

    def validate_depart_at(self, value: datetime | None) -> datetime | None:
        return value


class PlaceSerializer(serializers.Serializer):
    query = serializers.CharField()
    address = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class RouteSummarySerializer(serializers.Serializer):
    distance_miles = serializers.FloatField()
    duration_seconds = serializers.FloatField()
    duration_hours = serializers.FloatField()
    destination_eta = serializers.CharField()
    start = PlaceSerializer()
    finish = PlaceSerializer()


class FuelStopSerializer(serializers.Serializer):
    sequence = serializers.IntegerField()
    station_id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    price_per_gallon = serializers.FloatField()
    distance_from_start_miles = serializers.FloatField()
    gallons_purchased = serializers.FloatField()
    cost_usd = serializers.FloatField()
    remaining_range_before_refuel_miles = serializers.FloatField()
    eta = serializers.CharField()
    dwell_minutes = serializers.IntegerField()


class TripSummarySerializer(serializers.Serializer):
    total_gallons_used = serializers.FloatField()
    total_fuel_cost_usd = serializers.FloatField()
    average_price_per_gallon_usd = serializers.FloatField()
    stop_count = serializers.IntegerField()


class VehicleSerializer(serializers.Serializer):
    mpg = serializers.IntegerField()
    max_range_miles = serializers.IntegerField()
    tank_capacity_gallons = serializers.FloatField()
    range_reserve_miles = serializers.IntegerField()
    route_corridor_miles = serializers.FloatField()


class ExternalCallsSerializer(serializers.Serializer):
    geocode = serializers.IntegerField()
    routing = serializers.IntegerField()
    total = serializers.IntegerField()
    geocode_cache_hits = serializers.IntegerField()
    routing_cache_hits = serializers.IntegerField()
    per_station = serializers.IntegerField()


class MetaSerializer(serializers.Serializer):
    response_time_ms = serializers.FloatField()
    external_calls = ExternalCallsSerializer()
    stations_considered = serializers.IntegerField()
    stations_in_route_bbox = serializers.IntegerField()
    depart_at = serializers.CharField()
    currency_rounding = serializers.CharField()


class RoutePlanResponseSerializer(serializers.Serializer):
    """Documented success contract for POST /api/v1/route/."""

    route_summary = RouteSummarySerializer()
    route_geometry = serializers.DictField(
        help_text="GeoJSON LineString with [longitude, latitude] coordinates."
    )
    coordinates = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2),
        help_text="Polyline as [latitude, longitude] pairs for Leaflet-style maps.",
    )
    fuel_stops = FuelStopSerializer(many=True)
    trip_summary = TripSummarySerializer()
    vehicle = VehicleSerializer()
    meta = MetaSerializer()


class ErrorBodySerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    error = ErrorBodySerializer()
