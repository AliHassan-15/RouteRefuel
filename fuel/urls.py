from django.urls import path

from fuel.views import HealthView, RoutePlanView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("route/", RoutePlanView.as_view(), name="route-plan"),
]
