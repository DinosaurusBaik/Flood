import json
import os
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Flood Map Viewer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# Load data into memory for fast pagination
streamflow_data = {"features": [], "total": 0}

def load_data():
    file_path = os.path.join(DATA_DIR, "data_bersih_animasi.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                features = data.get("features", [])
                # Add an ID to each feature for easier reference
                for idx, feature in enumerate(features):
                    feature['id'] = idx
                
                streamflow_data["features"] = features
                streamflow_data["total"] = len(features)
                print(f"Loaded {streamflow_data['total']} features from data_bersih_animasi.json")
        except Exception as e:
            print(f"Error loading data: {e}")

# Load the data on startup
load_data()

@app.get("/api/streamflow")
def get_streamflow(page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=1000)):
    """
    Paginated endpoint for the streamflow data.
    """
    features = streamflow_data["features"]
    total = streamflow_data["total"]
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    paginated = features[start_idx:end_idx]
    
    return JSONResponse(content={
        "data": paginated,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit
        }
    })

# Mount static directories
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")
app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

# Serve index.html at root
@app.get("/")
def read_root():
    return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))

# Serve other static files from public if they are requested directly without /public prefix
@app.get("/{path:path}")
def serve_public(path: str):
    file_path = os.path.join(PUBLIC_DIR, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    # If not found, just return index to let JS handle or show 404
    return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))
