import json
import math

with open('preview_sumbar.json', 'r') as f:
    data = json.load(f)

# Build a dictionary of land points by (lon_round, lat_round)
land_points = {}
for f in data['features']:
    if f['properties'].get('location_type') == 'land':
        coords = f['geometry']['coordinates']
        # Round to 3 decimal places for matching (grid is about 0.0027 diff)
        lon, lat = round(coords[0], 3), round(coords[1], 3)
        land_points[(lon, lat)] = f

# The max streamflow point is [100.7165756225586, -0.53227424621582]
# let's round that: 100.717, -0.532
start_point = (100.717, -0.532)

path = []
current = start_point
visited = set()

while current:
    path.append(current)
    visited.add(current)
    # Find neighbors with streamflow < current streamflow
    lon, lat = current
    current_sf = land_points[current]['properties'].get('streamflow', 0)
    
    best_neighbor = None
    best_sf = -1
    
    # Grid steps are approx 0.003
    for dx in [-0.003, 0, 0.003]:
        for dy in [-0.003, 0, 0.003]:
            if dx == 0 and dy == 0: continue
            
            n_lon = round(lon + dx, 3)
            n_lat = round(lat + dy, 3)
            neighbor = (n_lon, n_lat)
            
            if neighbor in land_points and neighbor not in visited:
                n_sf = land_points[neighbor]['properties'].get('streamflow', 0)
                # To go upstream, we want the neighbor with the highest streamflow that is STRICTLY LESS than current_sf
                if n_sf < current_sf and n_sf > best_sf:
                    best_sf = n_sf
                    best_neighbor = neighbor
                    
    current = best_neighbor

print(f"Traced upstream path with {len(path)} points.")
for p in path[:10]:
    print(f"Coords: {p}, Streamflow: {land_points[p]['properties'].get('streamflow')}")
