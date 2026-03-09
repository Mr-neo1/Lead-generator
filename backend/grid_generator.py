from geopy.geocoders import Nominatim
import math

def generate_grid(location_name: str, radius_km: int, grid_size: str):
    geolocator = Nominatim(user_agent="lead_engine")
    location = geolocator.geocode(location_name)
    if not location:
        raise ValueError("Location not found")
    
    lat, lng = location.latitude, location.longitude
    rows, cols = map(int, grid_size.split('x'))
    
    # 1 degree latitude is approx 111 km
    lat_step = (radius_km / 111.0) / rows
    lng_step = (radius_km / (111.0 * math.cos(math.radians(lat)))) / cols
    
    coordinates = []
    for i in range(rows):
        for j in range(cols):
            grid_lat = lat + (i - rows/2) * lat_step
            grid_lng = lng + (j - cols/2) * lng_step
            coordinates.append((grid_lat, grid_lng))
            
    return coordinates
