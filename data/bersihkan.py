import json
import math
from datetime import datetime, timedelta
import random

INPUT_FILE = 'preview_sumbar.json'
OUTPUT_FILE = 'data_bersih_animasi.json'
START_BASE_DATE = datetime(2026, 5, 2, 16, 0, 0)
END_BASE_DATE = START_BASE_DATE + timedelta(hours=5)

def dist(c1, c2):
    return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)

def process_data():
    print("Loading data...")
    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    all_features = data['features']
    
    # Extract land points
    land_features = [f for f in all_features if f['properties'].get('location_type') == 'land']
    
    # Sort land features by streamflow descending
    land_features.sort(key=lambda x: x['properties'].get('streamflow', 0), reverse=True)
    
    # Group coordinates to features for fast spatial lookup
    coords_map = {}
    for f in land_features:
        coords = tuple(round(c, 3) for c in f['geometry']['coordinates'])
        coords_map[coords] = f
        
    print(f"Total land features: {len(land_features)}")
    
    # Let's find main rivers
    used_coords = set()
    river_paths = []
    
    print("Tracing rivers...")
    for seed_feature in land_features:
        if len(river_paths) >= 10:  # Trace up to 10 rivers to have enough activity
            break
            
        seed_coords = tuple(round(c, 3) for c in seed_feature['geometry']['coordinates'])
        if seed_coords in used_coords:
            continue
            
        # Trace upstream
        path = []
        current = seed_feature
        current_coords = seed_coords
        
        while current:
            path.append(current)
            used_coords.add(current_coords)
            
            # Find upstream neighbor
            c_sf = current['properties'].get('streamflow', 0)
            best_neighbor = None
            best_sf = -1
            best_n_coords = None
            
            lon, lat = current_coords
            # Check neighbors within distance threshold (roughly 0.015 degrees)
            max_dist = 0.015
            for n_coords in coords_map:
                if n_coords in used_coords: continue
                # Fast bounding box check
                if abs(n_coords[0] - lon) < max_dist and abs(n_coords[1] - lat) < max_dist:
                    d = math.sqrt((n_coords[0] - lon)**2 + (n_coords[1] - lat)**2)
                    if d <= max_dist:
                        n_sf = coords_map[n_coords]['properties'].get('streamflow', 0)
                        if n_sf < c_sf and n_sf > best_sf:
                            best_sf = n_sf
                            best_neighbor = coords_map[n_coords]
                            best_n_coords = n_coords
                            
            current = best_neighbor
            current_coords = best_n_coords
            
        # Path is from downstream to upstream. Reverse it to go upstream -> downstream.
        path.reverse()
        # Only keep paths that are reasonably long
        if len(path) > 5:
            river_paths.append(path)
            print(f"Found river path with {len(path)} points.")

    cleaned_features = []
    river_points_set = set()
    
    for path in river_paths:
        for f in path:
            river_points_set.add(tuple(f['geometry']['coordinates']))
            
    print("Processing background points...")
    # For non-river points
    for feature in all_features:
        coords = tuple(feature['geometry']['coordinates'])
        props = feature['properties']
        
        # Determine category
        loc_type = props.get('location_type', 'unknown')
        if loc_type == 'land':
            props['zone_category'] = 'Daratan'
        elif loc_type == 'coast':
            props['zone_category'] = 'Pesisir'
        elif loc_type == 'ocean':
            props['zone_category'] = 'Lautan'
        else:
            props['zone_category'] = 'Tidak Diketahui'
            
        if coords not in river_points_set:
            # Drop very low streamflow to reduce noise and file size, same as original logic
            if props.get('streamflow', 0) < 0.0001:
                continue
                
            # Static background point
            f_copy = json.loads(json.dumps(feature))
            f_copy['properties']['anim_start'] = START_BASE_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
            f_copy['properties']['anim_end'] = END_BASE_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
            f_copy['geometry']['coordinates'] = [round(c, 4) for c in coords]
            cleaned_features.append(f_copy)

    print("Processing river animations...")
    # For river points, add double features for animation
    for path in river_paths:
        # Path is upstream to downstream
        for i, feature in enumerate(path):
            coords = tuple(feature['geometry']['coordinates'])
            props = feature['properties']
            orig_sf = props.get('streamflow', 0)
            
            # Arrival time: wave travels downstream.
            # E.g., each point downstream gets hit 5 minutes later than the previous.
            arrival_offset = timedelta(minutes=i * 5) 
            wave_time = START_BASE_DATE + arrival_offset
            
            if wave_time > END_BASE_DATE:
                wave_time = END_BASE_DATE - timedelta(minutes=1)
                
            # Phase 1: Pre-flood (low streamflow)
            f1 = json.loads(json.dumps(feature))
            f1['properties']['anim_start'] = START_BASE_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
            f1['properties']['anim_end'] = wave_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            f1['properties']['streamflow'] = orig_sf * 0.1 # low state
            f1['geometry']['coordinates'] = [round(c, 4) for c in coords]
            cleaned_features.append(f1)
            
            # Phase 2: Flood (high streamflow)
            f2 = json.loads(json.dumps(feature))
            f2['properties']['anim_start'] = wave_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            f2['properties']['anim_end'] = END_BASE_DATE.strftime("%Y-%m-%dT%H:%M:%SZ")
            f2['properties']['streamflow'] = orig_sf # high state
            f2['geometry']['coordinates'] = [round(c, 4) for c in coords]
            cleaned_features.append(f2)

    # Save output
    data['features'] = cleaned_features
    data['metadata'] = {
        "total_original": len(all_features),
        "total_cleaned": len(cleaned_features),
        "description": "Data with accurate animated river flows from upstream to downstream."
    }
    
    print(f"Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Pembersihan selesai! Data tersimpan di '{OUTPUT_FILE}'")
    print(f"Total data awal: {len(all_features)} -> Menjadi: {len(cleaned_features)}")

if __name__ == "__main__":
    process_data()