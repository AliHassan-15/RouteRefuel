from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from fuel.serializers import (
    ErrorResponseSerializer,
    RoutePlanRequestSerializer,
    RoutePlanResponseSerializer,
)
from fuel.services.planner import TripPlannerService


class RoutePlanThrottle(AnonRateThrottle):
    scope = "route_plan"


class RoutePlanView(APIView):
    """
    Plan a USA driving route with cost-optimal fuel stops.

    External network budget: ≤ 3 calls cold (2× geocode + 1× route), often 0–1 when cached.
    Station selection uses the locally ingested fuel-price dataset only.
    """

    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [RoutePlanThrottle]

    @extend_schema(
        tags=["Route"],
        summary="Plan fuel-optimized USA route",
        description=(
            "Accepts free-text USA start/finish locations and returns route geometry, "
            "ordered cost-optimal fuel stops, trip cost summary, and timing/metrics meta."
        ),
        request=RoutePlanRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=RoutePlanResponseSerializer,
                description="Successful fuel route plan.",
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Validation / geocode / non-USA / no driving route.",
                examples=[
                    OpenApiExample(
                        "Geocode failed",
                        value={
                            "error": {
                                "code": "GEOCODE_FAILED",
                                "message": "Could not resolve location 'xyz'. Try a clearer USA place like 'City, ST' or a full street address.",
                                "details": {"query": "xyz"},
                            }
                        },
                    )
                ],
            ),
            422: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="No viable fuel stop within remaining vehicle range.",
            ),
            429: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Rate limit exceeded.",
            ),
            502: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="External geocoding or routing provider unavailable.",
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Fuel stations not loaded yet.",
            ),
        },
    )
    def post(self, request):
        serializer = RoutePlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        planner = TripPlannerService()
        result = planner.plan(
            data["start"],
            data["finish"],
            depart_at=data.get("depart_at"),
        )
        return Response(result, status=status.HTTP_200_OK)


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    @extend_schema(
        tags=["Health"],
        summary="Service health",
        responses={200: dict},
    )
    def get(self, request):
        from fuel.models import FuelStation

        total = FuelStation.objects.count()
        active = FuelStation.objects.filter(is_active=True).count()
        return Response(
            {
                "status": "ok",
                "stations_total": total,
                "stations_active": active,
            }
        )


class PlaceSuggestThrottle(AnonRateThrottle):
    scope = "place_suggest"


class PlaceSuggestView(APIView):
    """
    Typeahead for USA places.

    Uses the offline US cities index (same file as station ingest) so typing
    does not burn Nominatim quota. Returns labels like "Chicago, IL".
    """

    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [PlaceSuggestThrottle]

    @extend_schema(
        tags=["Places"],
        summary="Suggest USA places while typing",
        description=(
            "Prefix search over an offline USA cities index. "
            "Query with `q` (min 1 character) and optional `limit` (1–20)."
        ),
        responses={200: dict},
    )
    def get(self, request):
        from fuel.services.place_suggest import suggest_places

        query = str(request.query_params.get("q") or "").strip()
        try:
            limit = int(request.query_params.get("limit") or 12)
        except (TypeError, ValueError):
            limit = 12

        if len(query) < 1:
            return Response({"query": query, "suggestions": []})

        hits = suggest_places(query, limit=limit)
        return Response(
            {
                "query": query,
                "suggestions": [
                    {
                        "label": s.label,
                        "city": s.city,
                        "state": s.state,
                        "latitude": s.latitude,
                        "longitude": s.longitude,
                    }
                    for s in hits
                ],
            }
        )
