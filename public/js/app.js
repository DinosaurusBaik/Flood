// DOM Elements
const mapContainer = document.getElementById("map");
const tableBody = document.getElementById("table-body");
const btnPrev = document.getElementById("btn-prev");
const btnNext = document.getElementById("btn-next");
const pageInfo = document.getElementById("page-info");
const totalPointsEl = document.getElementById("total-points");

// State
let rawData = [];
let allFeatures = [];
let currentPage = 1;
const limit = 50;
let map;
let geoJsonLayer;
let markersLayer;
let activeMarker = null;
let currentMarkers = {}; // map feature id to marker layer

// Animation State
let minTime = 0;
let maxTime = 0;
let currentTime = 0;
let isPlaying = false;
let animationInterval;
let allRawFeatures = [];
let currentFilterMode = "all";
let globalMaxFlow = 0.01;

// Init Map
function initMap() {
  // Center of West Sumatra roughly
  map = L.map("map", {
    preferCanvas: true, // Use canvas for better performance with many points
  }).setView([-0.9, 100.5], 8);

  // Google Maps Satellite Hybrid TileLayer
  L.tileLayer(
    "http://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}",
    {
      attribution: '&copy; <a href="https://maps.google.com/">Google</a>',
      subdomains: ["mt0", "mt1", "mt2", "mt3"],
      maxZoom: 20,
    },
  ).addTo(map);
}

// Load Regional Polygon
async function loadRegion() {
  try {
    const response = await fetch("/data/regional-data.geojson");
    const data = await response.json();

    geoJsonLayer = L.geoJSON(data, {
      style: {
        color: "var(--accent-color)",
        weight: 2,
        opacity: 0.8,
        fillColor: "var(--accent-color)",
        fillOpacity: 0.1,
      },
    }).addTo(map);

    // Fit map to region
    map.fitBounds(geoJsonLayer.getBounds());
  } catch (e) {
    console.error("Error loading regional data:", e);
  }
}

// Load Streamflow Points
async function loadStreamflow() {
  try {
    // Cache-busting to ensure we load the newly processed JSON
    const response = await fetch(`/data/data_bersih_animasi.json?v=${Date.now()}`);
    const data = await response.json();

    allRawFeatures = data.features || [];

    let minT = Infinity;
    let maxT = -Infinity;

    // Add ID and Parse Timestamps
    allRawFeatures.forEach((f, i) => {
      f.id = i;
      const tStart = new Date(f.properties.anim_start).getTime();
      const tEnd = new Date(f.properties.anim_end).getTime();
      f.tStart = tStart;
      f.tEnd = tEnd;
      
      if (tStart < minT) minT = tStart;
      if (tEnd > maxT) maxT = tEnd;
    });

    minTime = minT;
    maxTime = maxT;
    currentTime = minTime;

    // Setup Slider
    const timeSlider = document.getElementById("time-slider");
    if (timeSlider && minTime !== Infinity) {
      timeSlider.min = minTime;
      timeSlider.max = maxTime;
      timeSlider.value = currentTime;
      timeSlider.disabled = false;
      updateTimeDisplay();
    }

    // Calculate Global Max Flow for stable colors
    if (allRawFeatures.length > 0) {
      const sortedFlows = allRawFeatures
        .map((f) => f.properties.streamflow)
        .sort((a, b) => a - b);
      const p98Index = Math.floor(sortedFlows.length * 0.98);
      globalMaxFlow = sortedFlows[p98Index] || 0.01;
    }

    applyFilter("all");
  } catch (e) {
    console.error("Error loading streamflow data:", e);
    tableBody.innerHTML =
      '<tr><td colspan="3" style="text-align:center;color:var(--danger)">Gagal memuat data. Pastikan server berjalan.</td></tr>';
  }
}

function applyFilter(mode) {
  currentFilterMode = mode;
  updateActiveFeatures();
}

function updateActiveFeatures() {
  let filtered = allRawFeatures;

  if (currentFilterMode === "land") {
    filtered = filtered.filter((f) => f.properties.location_type === "land");
  } else if (currentFilterMode === "coast") {
    filtered = filtered.filter((f) => f.properties.location_type === "coast");
  } else if (currentFilterMode === "ocean") {
    filtered = filtered.filter((f) => f.properties.location_type === "ocean");
  }

  // Filter by time
  allFeatures = filtered.filter((f) => currentTime >= f.tStart && currentTime <= f.tEnd);

  totalPointsEl.textContent = allFeatures.length.toLocaleString();
  currentPage = 1; // Reset to page 1 on filter/time change

  renderMapPoints();
  renderTable();
}

// Get color based on value and max value (Hydro Jet Colormap)
function getHydroColor(value, max) {
  let ratio = value / max;
  if (ratio > 1) ratio = 1;
  if (ratio < 0) ratio = 0;

  // Jet colormap: Blue -> Cyan -> Green -> Yellow -> Red
  let r = 0,
    g = 0,
    b = 0;
  if (ratio < 0.25) {
    r = 0;
    g = 4 * ratio;
    b = 1;
  } else if (ratio < 0.5) {
    r = 0;
    g = 1;
    b = 1 - 4 * (ratio - 0.25);
  } else if (ratio < 0.75) {
    r = 4 * (ratio - 0.5);
    g = 1;
    b = 0;
  } else {
    r = 1;
    g = 1 - 4 * (ratio - 0.75);
    b = 0;
  }
  return `rgb(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)})`;
}

// Render all points to map
function renderMapPoints() {
  if (markersLayer) map.removeLayer(markersLayer);

  markersLayer = L.layerGroup().addTo(map);

  const maxFlow = globalMaxFlow;

  allFeatures.forEach((feature) => {
    const coords = feature.geometry.coordinates;
    const latlng = [coords[1], coords[0]];
    const streamflow = feature.properties.streamflow;

    const pointColor = getHydroColor(streamflow, maxFlow);
    const ratio = Math.min(streamflow / maxFlow, 1);
    const radius = 2 + ratio * 4; // Larger radius for higher flow

    const marker = L.circleMarker(latlng, {
      radius: radius,
      fillColor: pointColor,
      color: pointColor,
      weight: 0,
      opacity: 1,
      fillOpacity: 0.8,
    });

    marker.bindPopup(`
            <div class="custom-popup-title">Streamflow Point #${feature.id}</div>
            <div class="custom-popup-stat">
                <span>Streamflow:</span>
                <strong>${streamflow.toFixed(6)}</strong>
            </div>
            <div class="custom-popup-stat">
                <span>Lat:</span>
                <strong>${coords[1].toFixed(4)}</strong>
            </div>
            <div class="custom-popup-stat">
                <span>Lng:</span>
                <strong>${coords[0].toFixed(4)}</strong>
            </div>
        `);

    marker.on("click", () => {
      highlightTableRow(feature.id);
    });

    currentMarkers[feature.id] = marker;
    markersLayer.addLayer(marker);
  });
}

// Render Table
function renderTable() {
  tableBody.innerHTML = "";

  const totalPages = Math.ceil(allFeatures.length / limit);
  const startIdx = (currentPage - 1) * limit;
  const endIdx = Math.min(startIdx + limit, allFeatures.length);

  const pageFeatures = allFeatures.slice(startIdx, endIdx);

  if (pageFeatures.length === 0) {
    tableBody.innerHTML =
      '<tr><td colspan="3" style="text-align:center">Data kosong.</td></tr>';
  } else {
    pageFeatures.forEach((f) => {
      const tr = document.createElement("tr");
      tr.id = `row-${f.id}`;

      const coords = f.geometry.coordinates;

      tr.innerHTML = `
                <td>#${f.id}</td>
                <td>${coords[1].toFixed(4)}, ${coords[0].toFixed(4)}</td>
                <td>${f.properties.streamflow.toFixed(6)}</td>
            `;

      tr.addEventListener("click", () => {
        focusOnMarker(f.id);
      });

      tableBody.appendChild(tr);
    });
  }

  // Update pagination UI
  pageInfo.textContent = `Page ${currentPage} / ${totalPages}`;
  btnPrev.disabled = currentPage === 1;
  btnNext.disabled = currentPage === totalPages || totalPages === 0;
}

// Interactions
function focusOnMarker(id) {
  highlightTableRow(id);

  const marker = currentMarkers[id];
  if (marker) {
    map.flyTo(marker.getLatLng(), 12, { duration: 1.5 });
    marker.openPopup();
  }
}

function highlightTableRow(id) {
  // Remove active class from all rows
  document.querySelectorAll("#table-body tr").forEach((tr) => {
    tr.classList.remove("active");
  });

  // Add active class to target row
  const targetRow = document.getElementById(`row-${id}`);
  if (targetRow) {
    targetRow.classList.add("active");
    targetRow.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } else {
    // If row is not on current page, we need to switch page
    const targetPage = Math.floor(id / limit) + 1;
    if (targetPage !== currentPage) {
      currentPage = targetPage;
      renderTable();
      // Highlight again after rendering
      setTimeout(() => {
        const newRow = document.getElementById(`row-${id}`);
        if (newRow) {
          newRow.classList.add("active");
          newRow.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 50);
    }
  }
}

// Event Listeners
btnPrev.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    renderTable();
  }
});

btnNext.addEventListener("click", () => {
  const totalPages = Math.ceil(allFeatures.length / limit);
  if (currentPage < totalPages) {
    currentPage++;
    renderTable();
  }
});

// Filter Event Listeners
const btnFilterAll = document.getElementById("btn-filter-all");
const btnFilterLand = document.getElementById("btn-filter-land");
const btnFilterCoast = document.getElementById("btn-filter-coast");
const btnFilterOcean = document.getElementById("btn-filter-ocean");

function clearActiveFilters() {
  [btnFilterAll, btnFilterLand, btnFilterCoast, btnFilterOcean].forEach(
    (btn) => {
      if (btn) btn.classList.remove("active");
    },
  );
}

btnFilterAll.addEventListener("click", () => {
  clearActiveFilters();
  btnFilterAll.classList.add("active");
  applyFilter("all");
});

btnFilterLand.addEventListener("click", () => {
  clearActiveFilters();
  btnFilterLand.classList.add("active");
  applyFilter("land");
});

btnFilterCoast.addEventListener("click", () => {
  clearActiveFilters();
  btnFilterCoast.classList.add("active");
  applyFilter("coast");
});

btnFilterOcean.addEventListener("click", () => {
  clearActiveFilters();
  btnFilterOcean.classList.add("active");
  applyFilter("ocean");
});

// Boot
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadRegion();
  loadStreamflow();
  
  // Setup Animation Event Listeners
  const timeSlider = document.getElementById("time-slider");
  const btnPlayPause = document.getElementById("btn-play-pause");
  
  if (timeSlider) {
    timeSlider.addEventListener("input", (e) => {
      currentTime = parseInt(e.target.value);
      updateTimeDisplay();
      updateActiveFeatures();
    });
  }

  if (btnPlayPause) {
    btnPlayPause.addEventListener("click", () => {
      if (isPlaying) {
        pauseAnimation();
      } else {
        playAnimation();
      }
    });
  }
});

function playAnimation() {
  isPlaying = true;
  const btnPlayPause = document.getElementById("btn-play-pause");
  if (btnPlayPause) {
    btnPlayPause.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>';
  }
  
  // Advance time
  const totalDuration = maxTime - minTime;
  const step = totalDuration / 500; // Total 500 ticks for smooth fast loop
  
  animationInterval = setInterval(() => {
    currentTime += step;
    if (currentTime > maxTime) {
      currentTime = minTime; // Loop back
      pauseAnimation(); // Optional: pause at end
      return;
    }
    
    const timeSlider = document.getElementById("time-slider");
    if (timeSlider) timeSlider.value = currentTime;
    
    updateTimeDisplay();
    updateActiveFeatures();
  }, 100);
}

function pauseAnimation() {
  isPlaying = false;
  clearInterval(animationInterval);
  const btnPlayPause = document.getElementById("btn-play-pause");
  if (btnPlayPause) {
    btnPlayPause.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon-play"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';
  }
}

function updateTimeDisplay() {
  const timeDisplay = document.getElementById("current-time-display");
  if (timeDisplay) {
    const d = new Date(currentTime);
    // Format: DD MMM YYYY, HH:mm
    timeDisplay.textContent = d.toLocaleString('id-ID', { 
      day: 'numeric', month: 'short', year: 'numeric', 
      hour: '2-digit', minute: '2-digit' 
    });
  }
}
