import json

with open('preview_sumbar.json', 'r') as f:
    data = json.load(f)

land_features = [f for f in data['features'] if f['properties'].get('location_type') == 'land']
land_features.sort(key=lambda x: x['properties'].get('streamflow', 0), reverse=True)

print('Top 20 highest streamflow points on land:')
for i, f in enumerate(land_features[:20]):
    coords = f['geometry']['coordinates']
    streamflow = f['properties'].get('streamflow')
    print(f"#{i+1}: Coords {coords}, Streamflow {streamflow}")
