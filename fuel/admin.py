from django.contrib import admin

from fuel.models import FuelStation, GeocodeCache

admin.site.register(FuelStation)
admin.site.register(GeocodeCache)
