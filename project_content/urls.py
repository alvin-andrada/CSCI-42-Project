from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path("", views.login_view, name='login'),
    path('register', views.register, name="register"),
    path('user-logout', views.user_logout, name="user-logout"),
    path("home", views.home, name='home'), 
    path('profile', views.profile_view, name='profile'),
    path("geocoding/<int:pk>", GeocodingView.as_view(), name='geocoding'), 
    path("distance", DistanceView.as_view(), name='distance'), 
    path("map", MapView.as_view(), name='map'), 
    path("route_create", Route_CreateView.as_view(), name='my_route_view'),
    path('room-create', views.CreateRoom, name='create-room'),
    path('<str:room_name>/<str:username>/', views.MessageView, name='room'),
   
]