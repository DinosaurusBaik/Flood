import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export default function MapContainerComponent() {
  return (
    <div style={{ height: "100%", width: "100%" }}>
      <MapContainer 
        center={[-0.947, 100.417]} 
        zoom={8} 
        scrollWheelZoom={true}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap'
        />
        <Marker position={[-0.947, 100.417]}>
          <Popup>Titik Awal EWS Sumbar</Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}