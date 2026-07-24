from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class AppError(Exception):
    """Domain error mapped to a clean JSON API response."""

    code = "APP_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    status_code = status.HTTP_400_BAD_REQUEST


class GeocodeFailed(AppError):
    code = "GEOCODE_FAILED"
    status_code = status.HTTP_400_BAD_REQUEST


class GeocodingUnavailable(AppError):
    code = "GEOCODING_UNAVAILABLE"
    status_code = status.HTTP_502_BAD_GATEWAY


class LocationNotInUSA(AppError):
    code = "LOCATION_NOT_IN_USA"
    status_code = status.HTTP_400_BAD_REQUEST


class NoDrivingRoute(AppError):
    code = "NO_DRIVING_ROUTE"
    status_code = status.HTTP_400_BAD_REQUEST


class NoFeasibleFuelPlan(AppError):
    code = "NO_FEASIBLE_FUEL_PLAN"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class StationsNotReady(AppError):
    code = "STATIONS_NOT_READY"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class RoutingUnavailable(AppError):
    code = "ROUTING_UNAVAILABLE"
    status_code = status.HTTP_502_BAD_GATEWAY


class RateLimited(AppError):
    code = "RATE_LIMITED"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


def api_exception_handler(exc, context):
    from rest_framework.exceptions import Throttled

    if isinstance(exc, Throttled):
        wait = getattr(exc, "wait", None)
        return Response(
            {
                "error": {
                    "code": "RATE_LIMITED",
                    "message": "Too many requests. Please slow down and retry.",
                    "details": {"retry_after_seconds": wait},
                }
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    if isinstance(exc, AppError):
        return Response(
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
            status=exc.status_code,
        )

    response = exception_handler(exc, context)
    if response is not None:
        return Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request. Check start, finish, and optional depart_at.",
                    "details": response.data,
                }
            },
            status=response.status_code,
        )
    return response
