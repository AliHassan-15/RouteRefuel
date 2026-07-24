from django.urls import path

from fuel.views import HealthView, PlaceSuggestView, RoutePlanView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("route/", RoutePlanView.as_view(), name="route-plan"),
    path("places/suggest/", PlaceSuggestView.as_view(), name="place-suggest"),
]
