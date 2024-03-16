from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path("", views.login_view, name='login'),
    path('register', views.register, name="register"),
    path('user-logout', views.user_logout, name="user-logout"),
    path("home", HomeView.as_view(), name='my_home_view'), 
    path("geocoding/<int:pk>", GeocodingView.as_view(), name='my_geocoding_view'), 
    path("distance", DistanceView.as_view(), name='my_distance_view'), 
    path("map", MapView.as_view(), name='my_map_view'), 
   
   

]