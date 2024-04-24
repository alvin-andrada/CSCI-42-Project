from django.forms import modelformset_factory
import json
from django.views.generic import ListView
from django.views import View
from django.shortcuts import render, redirect
from .models import *
import googlemaps
from django.conf import settings
from .forms import *
from datetime import datetime
from django.db.models import F

from django.contrib.auth.models import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

def register(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")

    context = {'registerform':form}
    return render(request, 'project_content/register.html', context=context)


def login_view(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect("home")
            
    context = {'loginform':form}
    return render(request, 'project_content/login.html', context=context)


def user_logout(request):
    auth.logout(request)
    return redirect("login")

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    password_form = PasswordChangeForm(user=request.user)

    context = {
        'form': form,
        'password_form': password_form,
    }
    return render(request, 'project_content/profile.html', context)

@login_required
def home(request):
    user = request.user
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            user_location = UserLocation.objects.get(user=user)
            user_location.user_location = location.user_location
            user_location.save()
            return redirect('home')
    else:
        form = LocationForm()
    return render(request, 'project_content/home.html', {'form': form})

# class HomeView(LoginRequiredMixin, ListView):
#     template_name = "project_content/home.html"
#     context_object_name = 'mydata'
#     model = Locations
#     success_url = "/"

class MapView(View): 
    template_name = "project_content/map.html"

    def get(self,request): 
        key = settings.GOOGLE_API_KEY
        eligable_locations = Locations.objects.filter(place_id__isnull=False)
        locations = []

        for a in eligable_locations: 
            data = {
                'lat': float(a.lat), 
                'lng': float(a.lng), 
                'name': a.name
            }

            locations.append(data)


        context = {
            "key":key, 
            "locations": locations
        }

        return render(request, self.template_name, context)
    

def find_nearby_locations(latitude, longitude, max_distance_km=10):
    """
    Find locations near a given latitude and longitude within a specified distance
    """
    # Calculate the min and max latitude and longitude values for the bounding box
    # around the central point (latitude, longitude)
    lat_min = latitude - (max_distance_km / 111.32)
    lat_max = latitude + (max_distance_km / 111.32)
    lon_min = longitude - (max_distance_km / (111.32 * math.cos(math.radians(latitude))))
    lon_max = longitude + (max_distance_km / (111.32 * math.cos(math.radians(latitude))))

    # Filter locations within the bounding box
    nearby_locations = Locations.objects.filter(lat__range=(lat_min, lat_max), 
                                                 lng__range=(lon_min, lon_max))

    # Calculate the distance between each location and the central point
    # and annotate the queryset with the distance
    nearby_locations = nearby_locations.annotate(distance=F('distance_km'))

    # Filter locations within the specified distance
    nearby_locations = nearby_locations.filter(distance__lte=max_distance_km)

    # Sort locations by distance
    nearby_locations = nearby_locations.order_by('distance')

    return nearby_locations


class DistanceView(View):
    template_name = "project_content/distance.html"

    def get(self, request): 
        form = DistanceForm
        distances = Distances.objects.all()
        context = {
            'form':form,
            'distances':distances
        }

        return render(request, self.template_name, context)

    def post(self, request): 
        form = DistanceForm(request.POST)
        if form.is_valid(): 
            from_location = form.cleaned_data['from_location']
            from_location_info = Locations.objects.get(name=from_location)
            from_adress_string = str(from_location_info.adress)+", "+str(from_location_info.zipcode)+", "+str(from_location_info.city)+", "+str(from_location_info.country)

            to_location = form.cleaned_data['to_location']
            to_location_info = Locations.objects.get(name=to_location)
            to_adress_string = str(to_location_info.adress)+", "+str(to_location_info.zipcode)+", "+str(to_location_info.city)+", "+str(to_location_info.country)

            mode = form.cleaned_data['mode']
            now = datetime.now()

            gmaps = googlemaps.Client(key= settings.GOOGLE_API_KEY)
            calculate = gmaps.distance_matrix(
                    from_adress_string,
                    to_adress_string,
                    mode = mode,
                    departure_time = now
            )


            duration_seconds = calculate['rows'][0]['elements'][0]['duration']['value']
            duration_minutes = duration_seconds/60

            distance_meters = calculate['rows'][0]['elements'][0]['distance']['value']
            distance_kilometers = distance_meters/1000

            if 'duration_in_traffic' in calculate['rows'][0]['elements'][0]: 
                duration_in_traffic_seconds = calculate['rows'][0]['elements'][0]['duration_in_traffic']['value']
                duration_in_traffic_minutes = duration_in_traffic_seconds/60
            else: 
                duration_in_traffic_minutes = None

            
            obj = Distances(
                from_location = Locations.objects.get(name=from_location),
                to_location = Locations.objects.get(name=to_location),
                mode = mode,
                distance_km = distance_kilometers,
                duration_mins = duration_minutes,
                duration_traffic_mins = duration_in_traffic_minutes
            )

            obj.save()

        else: 
            print(form.errors)
        
        return redirect('distance')


class GeocodingView(View):
    template_name = "project_content/geocoding.html"

    def get(self,request,pk): 
        location = Locations.objects.get(pk=pk)

        if location.lng and location.lat and location.place_id != None: 
            lat = location.lat
            lng = location.lng
            place_id = location.place_id
            label = "from my database"

        elif location.adress and location.country and location.zipcode and location.city != None: 
            adress_string = str(location.adress)+", "+str(location.zipcode)+", "+str(location.city)+", "+str(location.country)

            gmaps = googlemaps.Client(key = settings.GOOGLE_API_KEY)
            result = gmaps.geocode(adress_string)[0]
            
            lat = result.get('geometry', {}).get('location', {}).get('lat', None)
            lng = result.get('geometry', {}).get('location', {}).get('lng', None)
            place_id = result.get('place_id', {})
            label = "from my api call"

            location.lat = lat
            location.lng = lng
            location.place_id = place_id
            location.save()

        else: 
            result = ""
            lat = ""
            lng = ""
            place_id = ""
            label = "no call made"

        context = {
            'location':location,
            'lat':lat, 
            'lng':lng, 
            'place_id':place_id, 
            'label': label
        }
        
        return render(request, self.template_name, context)

class Route_CreateView(View):
    template_name="project_content/route_create.html"
    display="project_content/route_display.html"

    key = settings.GOOGLE_API_KEY

    def get(self, request):
        form = DriverForm()
        passengerSet = modelformset_factory(Locations, form=PassengerForm, extra=1)
        passenger = passengerSet(queryset=Locations.objects.none())

        context = {
            'driver': form,
            'passengerFormset': passenger
        }

        return render(request, self.template_name, context)
    
    def post(self, request):
        driver = DriverForm(request.POST)
        passengerFormset = modelformset_factory(Locations, form=PassengerForm, extra=2)
        passengerForm = passengerFormset(request.POST)
        
        if driver.is_valid():
            origin = driver.cleaned_data['origin']
            destination = driver.cleaned_data['destination']
            origin_placeid = Locations.objects.get(name=origin).place_id
            destination_placeid = Locations.objects.get(name=destination).place_id
        
        passenger_list = []
        for passenger in passengerForm:
            if passenger.is_valid():
                data = passenger.cleaned_data["passenger"]
                passenger_placeid = Locations.objects.get(name=data).place_id
                waypoint = {"location": {"placeId": passenger_placeid},"stopover": True}
                passenger_list.append(waypoint)

        key=settings.GOOGLE_API_KEY
        context = {
            "google_api_key": key,
            "origin": origin,
            "destination": destination,
            "waypoints": json.dumps(passenger_list),
            "origin_placeid": origin_placeid,
            "destination_placeid": destination_placeid,
        }

        return render(request, self.display, context)
        # return render(request, self.template_name, context)
        
# class MapView(View):
#     def get(self, request):
#         form = LocationForm()
#         return render(request, 'project_content/select_route.html', {'form': form})
    
#     def post(self, request):
#         form = LocationForm(request.POST)
#         if form.is_valid():
#             google_api_key = settings.GOOGLE_API_KEY
#             origin = form.cleaned_data['origin']
#             destination = form.cleaned_data['destination']
#             waypoint = form.cleaned_data.get('waypoint')  # Get the selected waypoint, if any
            
#             # Initialize Google Maps client with your API key
#             gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)
            
#             # Define the waypoints list for the API request
#             waypoints = [waypoint.address] if waypoint else None
            
#             # Make API request to get directions
#             directions_result = gmaps.directions(origin.address, destination.address, mode="driving", waypoints=waypoints)
            
#             # Extract route information
#             route_info = directions_result[0]['legs'][0]
#             distance_km = route_info['distance']['value'] / 1000  # Convert meters to kilometers
#             duration_mins = route_info['duration']['value'] / 60  # Convert seconds to minutes
            
#             # Render the route page with route information
#             return render(request, 'project_content/route.html', {'google_api_key': google_api_key, 'origin': origin, 'destination': destination, 
#                                                   'distance_km': distance_km, 'duration_mins': duration_mins,
#                                                   'waypoint': waypoint})
    
#         # If form is not valid or if the request is not POST, redirect to home page
#         return redirect('home')

def CreateRoom(request):
    if request.method == 'POST':
        username = request.POST['username']
        room = request.POST['room']

        try:
            get_room = Room.objects.get(room_name=room)
        except Room.DoesNotExist:
            new_room = Room(room_name=room)
            new_room.save()

        return redirect('room', room_name=room, username=username)

    return render(request, 'project_content/room.html')

def MessageView(request, room_name, username):
    get_room = Room.objects.get(room_name=room_name)
    get_messages = Message.objects.filter(room=get_room)
    
    context = {
        "messages": get_messages,
        "user": username,
        "room_name": room_name,
    }
    
    return render(request, 'project_content/message.html', context)