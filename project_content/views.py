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
            try:
                user_location = UserLocation.objects.get(user=user)
            except:
                user_location = UserLocation(user=user)
            user_location.user_location = location.user_location
            user_location.save()
            return redirect('home')
    else:
        form = LocationForm()
    return render(request, 'project_content/home.html', {'form': form, 'locations': Locations.objects.all()})

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
    

class DestinationRequestsView(View):
    template_name = "project_content/destination_requests.html"

    def get(self, request): 
        form = DestinationRequestForm()

        context = {
            'form': form,
            'data': DestinationRequest.objects.all(),
            'user_locations': UserLocation.objects.all()
        }

        return render(request, self.template_name, context)
    
    def post(self, request):
        form = DestinationRequestForm(request.POST)
        user = request.user
        if form.is_valid():
            form_destination = form.save(commit=False)
            try:
                destination_request = DestinationRequest.objects.get(user=user)
            except:
                destination_request = DestinationRequest(user=user)
            destination_request.destination = form_destination.destination
            destination_request.save()
            return redirect('destination_requests')


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
        # passengerSet = modelformset_factory(Locations, form=PassengerForm, extra=1)
        # passenger = passengerSet(queryset=Locations.objects.none())
        passengers = PassengerForm()

        context = {
            'driver': form,
            'passengers': passengers
        }

        return render(request, self.template_name, context)
    

    def get_passenger_rating(self, origin_location, destination_location, passenger_location):
        o = (float(origin_location.lat), float(origin_location.lng))
        d = (float(destination_location.lat), float(destination_location.lng))
        p = (float(passenger_location.lat), float(passenger_location.lng))

        # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
        # lat = x, lng = y, distance does not matter either way
        num = abs( (d[0] - o[0]) * (p[1] - o[1]) - (p[0] - o[0]) * (d[1] - o[1]) )
        num *= 1000 # for scaling
        den = ( (d[0] - o[0]) ** 2 + (d[1] - o[1]) ** 2 ) ** 0.5

        return num / den

    
    def post(self, request):
        driver = DriverForm(request.POST)
        passengers = PassengerForm(request.POST)
        # passengerFormsetF = modelformset_factory(Locations, form=PassengerForm, extra=2)
        # passengerFormset = passengerFormsetF(request.POST)
        
        
        if driver.is_valid():
            origin = driver.cleaned_data['origin']
            destination = driver.cleaned_data['destination']
            origin_placeid = Locations.objects.get(name=origin).place_id
            destination_placeid = Locations.objects.get(name=destination).place_id
        
        gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)

        origin_geocode = gmaps.geocode(origin)[0]
        origin_coords = []
        origin_coords.append(origin_geocode.get('geometry', {}).get('location', {}).get('lat', None))
        origin_coords.append(origin_geocode.get('geometry', {}).get('location', {}).get('lng', None))
        origin_coords = tuple(origin_coords)

        destination_geocode = gmaps.geocode(destination)[0]
        destination_coords = []
        destination_coords.append(destination_geocode.get('geometry', {}).get('location', {}).get('lat', None))
        destination_coords.append(destination_geocode.get('geometry', {}).get('location', {}).get('lng', None))
        destination_coords = tuple(destination_coords)

        





        if passengers.is_valid():
            passenger_users = passengers.cleaned_data['passenger'].split(', ')
            
            users_dict = {}
            for u in User.objects.all():
                users_dict[u.username] = u

            user_locations_dict = {}
            for ul in UserLocation.objects.all():
                user_locations_dict[ul.user] = ul.user_location

            locations_dict = {}
            for l in Locations.objects.all():
                locations_dict[l.name] = l

            usernames_list = passenger_users


            passenger_limit = 2
            filtered_destination_requests = DestinationRequest.objects.filter(destination=destination)
            filtered_destination_requests_users = [f.user for f in filtered_destination_requests]
            passenger_scores = {}

            for u in filtered_destination_requests_users:
                passenger_scores[u] = self.get_passenger_rating(origin, destination, locations_dict[user_locations_dict[u]])

            passenger_limit = min(passenger_limit, len(filtered_destination_requests_users)) # if num of requests for a destination is less than limit

            passenger_users = []
            for _ in range(passenger_limit): # get <passenger_limit> lowest passenger scores
                passenger_users.append( min(passenger_scores, key=passenger_scores.get) )
                passenger_scores[passenger_users[-1]] = float('inf')

            
            passenger_locs = [user_locations_dict[u] for u in passenger_users]
            passenger_locs = [locations_dict[p] for p in passenger_locs]

            
        i = 0
        passenger_coords = {}
        passenger_placeids = {}
        for p in passenger_locs:
            i += 1
            passenger_geocode = gmaps.geocode(p)[0]
            passenger_coords[p] = tuple([
                passenger_geocode.get('geometry', {}).get('location', {}).get('lat', None),
                passenger_geocode.get('geometry', {}).get('location', {}).get('lng', None)
            ])

            passenger_placeids[p] = passenger_geocode['place_id']
            

        route = [origin]
        route_properties = []

        passenger_list = []
        next_leg_choices = {}
        next_leg_choices_times = {}
        for p in passenger_locs:
            calculate = gmaps.distance_matrix(
                origin_coords,
                passenger_coords[p],
                mode = "driving",
                departure_time = datetime.now()
            )
            next_leg_choices[p] = calculate['rows'][0]['elements'][0]['distance']['value'] / 1000
            next_leg_choices_times[p] = (calculate['rows'][0]['elements'][0]['duration']['value'] / 60, calculate['rows'][0]['elements'][0]['distance']['value'] / 1000, f"{route[-1].name} to {p.name}")
            passenger_list.append(passenger_placeids[p])
        route.append(min(next_leg_choices, key=next_leg_choices.get))
        route_properties.append(next_leg_choices_times[route[-1]])

        while len(route) <= len(passenger_locs):
            next_leg_choices = {}
            for p in passenger_locs:
                if p not in route:
                    calculate = gmaps.distance_matrix(
                        passenger_coords[route[-1]],
                        passenger_coords[p],
                        mode = "driving",
                        departure_time = datetime.now()
                    )
                    next_leg_choices[p] = calculate['rows'][0]['elements'][0]['distance']['value'] / 1000
                    next_leg_choices_times[p] = (calculate['rows'][0]['elements'][0]['duration']['value'] / 60, calculate['rows'][0]['elements'][0]['distance']['value'] / 1000, f"{route[-1].name} to {p}")
            route.append(min(next_leg_choices, key=next_leg_choices.get))
            route_properties.append(next_leg_choices_times[route[-1]])
        route.append(destination)

        calculate = gmaps.distance_matrix(
            passenger_coords[route[-2]],
            destination_coords,
            mode = "driving",
            departure_time = datetime.now()
        )
        route_properties.append((calculate['rows'][0]['elements'][0]['duration']['value'] / 60, calculate['rows'][0]['elements'][0]['distance']['value'] / 1000, f"{route[-2].name} to {route[-1].name}"))

        total_distance = 0
        total_duration = 0
        for p in route_properties:
            total_duration += p[0]
            total_distance += p[1]
        total_duration = round(total_duration)
        total_distance = round(total_distance, 1)
        route_properties = [f"{p[2]}: {round(p[1], 1)} km, {round(p[0])} mins" for p in route_properties]
        
        
            

        
        passenger_list = [{"location": {"placeId": passenger_placeid},"stopover": True} for passenger_placeid in passenger_list]
        # waypoint = {"location": {"placeId": passenger_placeid},"stopover": True}
        # passenger_list.append(waypoint)

        context = {
            "google_api_key": settings.GOOGLE_API_KEY,
            "origin": origin,
            "destination": destination,
            "waypoints": json.dumps(passenger_list),
            "origin_placeid": origin_placeid,
            "destination_placeid": destination_placeid,
            "distance_km": calculate['rows'][0]['elements'][0]['distance']['value'] / 1000,
            "duration_mins": calculate['rows'][0]['elements'][0]['duration']['value'] / 60,
            "passenger_list": passenger_list[0]['location']['placeId'],
            "passenger_coords": passenger_coords,
            "passenger_limit": passenger_limit,
            "passenger_locations": [f"{passenger_locs[i]} - {passenger_users[i]}" for i in range(len(passenger_users))],
            "route_properties": route_properties,
            "total_duration": total_duration,
            "total_distance": total_distance,
        }

        # raise SystemError # for debugging to view local vars in django

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