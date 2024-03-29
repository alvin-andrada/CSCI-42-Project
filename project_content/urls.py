from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path("", views.login_view, name='login'),
    path('register', views.register, name="register"),
    path('user-logout', views.user_logout, name="user-logout"),
    path("home", HomeView.as_view(), name='home'), 
    path('profile', views.profile_view, name='profile'),
    path("geocoding/<int:pk>", GeocodingView.as_view(), name='geocoding'), 
    path("distance", DistanceView.as_view(), name='distance'), 
    path("map", MapView.as_view(), name='map'), 
   
   

]