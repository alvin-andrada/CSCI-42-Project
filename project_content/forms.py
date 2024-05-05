from django import forms 
from django.forms import ModelForm
from .models import *

# User authentication imports
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from django.forms.widgets import PasswordInput, TextInput


modes = (
    ("driving", "driving"), 
    ("walking", "walking"),
    ("bicycling", "bicycling"),
    ("transit", "transit")
)

# - Create/Register a user
class CreateUserForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

# - Authenticate a user
class LoginForm(AuthenticationForm):

    username = forms.CharField(widget=TextInput())
    password = forms.CharField(widget=PasswordInput())

class ProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class DistanceForm(ModelForm): 
    from_location = forms.ModelChoiceField(label="Location from", required=True, queryset=Locations.objects.all())
    to_location = forms.ModelChoiceField(label="Location to", required=True, queryset=Locations.objects.all())
    mode = forms.ChoiceField(choices=modes, required=True)
    class Meta: 
        model = Distances
        exclude = ['created_at', 'edited_at', 'distance_km','duration_mins','duration_traffic_mins']

class DriverForm(ModelForm):
    origin = forms.ModelChoiceField(label="origin", required=True, queryset=Locations.objects.all())
    destination = forms.ModelChoiceField(label="destination", required=True, queryset=Locations.objects.all())
    class Meta:
        model = Locations
        fields = ['lat', 'lng']

class PassengerForm(ModelForm):
    # passenger = forms.ModelChoiceField(label="passenger", required=False, queryset=Locations.objects.all())
    passenger = forms.CharField(label="passenger", widget=TextInput(), required=True)
    class Meta:
        model = Locations
        # fields = ['lat', 'lng']
        fields = []
        # exclude = '__all__'

class LocationForm(forms.ModelForm):
    class Meta:
        model = UserLocation
        fields = ('user_location',)