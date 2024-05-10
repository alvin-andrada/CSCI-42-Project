from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Locations)
admin.site.register(Room)
admin.site.register(Message)
admin.site.register(UserLocation)
admin.site.register(DestinationRequest)