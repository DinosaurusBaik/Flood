import json
import os
from global_land_mask import globe

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "preview_sumbar.json")

def is_coast(lat, lon, step=0.03):
    # Check 4 neighbors at a distance of ~3km (0.03 degrees)
    center = globe.is_land(lat, lon)
    neighbors = [
        globe.is_land(lat + step, lon),
        globe.is_land(lat - step, lon),
        globe.is_land(lat, lon + step),
        globe.is_land(lat, lon - step)
    ]
    # If the center differs from ANY of its neighbors, it's on a boundary (coast)
    if any(n != center for n in neighbors):
        return True
    return False

def process_land_mask():
    print(f"Reading {DATA_FILE}...")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    features = data.get("features", [])
    print(f"Loaded {len(features)} features. Processing location types...")
    
    counts = {"land": 0, "coast": 0, "ocean": 0}
    
    for feature in features:
        lon, lat = feature["geometry"]["coordinates"]
        
        # Determine base land/ocean
        is_land = globe.is_land(lat, lon)
        
        # Determine if it's coastal
        if is_coast(lat, lon):
            location_type = "coast"
        elif is_land:
            location_type = "land"
        else:
            location_type = "ocean"
            
        feature["properties"]["location_type"] = location_type
        counts[location_type] += 1
            
    print(f"Categorization complete:")
    print(f"- Land: {counts['land']}")
    print(f"- Coast: {counts['coast']}")
    print(f"- Ocean: {counts['ocean']}")
    
    print(f"Saving {DATA_FILE}...")
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f)
        
    print("Done!")

if __name__ == "__main__":
    process_land_mask()
