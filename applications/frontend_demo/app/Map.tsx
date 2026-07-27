'use client';

import { useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default function Map({ geoData }: { geoData: any }) {
  useEffect(() => {
    // This ensures Leaflet only tries to change the icons when the browser is fully loaded,
    // avoiding crashes during startup.
    if (typeof window !== 'undefined') {
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      });
    }
  }, []);

  const onEachFeature = (feature: any, layer: L.Layer) => {
    if (feature.properties) {
      // Destructure handling both Portuguese (original geojson) and English (from DB query) property names
      const { Nome, Name, Endereço, Address, Cidade, City, CEP, state, Telefone, Phone } = feature.properties;
      
      const displayName = Name || Nome || 'Unknown Agency';
      const displayAddress = Address || Endereço || 'N/A';
      const displayCity = City || Cidade || 'N/A';
      const displayZip = feature.properties['ZIP Code'] || CEP || 'N/A';
      const displayPhone = Phone || Telefone || 'N/A';
      const displayState = state || 'AL';

      const popupContent = `
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
          <h4 style="margin-top: 0; margin-bottom: 8px; color: #001529;">${displayName}</h4>
          <p style="margin: 4px 0; font-size: 13px;"><strong>Address:</strong> ${displayAddress}</p>
          <p style="margin: 4px 0; font-size: 13px;"><strong>City:</strong> ${displayCity} - ${displayState}</p>
          <p style="margin: 4px 0; font-size: 13px;"><strong>ZIP Code:</strong> ${displayZip}</p>
          <p style="margin: 4px 0; font-size: 13px;"><strong>Phone:</strong> ${displayPhone}</p>
        </div>
      `;
      layer.bindPopup(popupContent);
    }
  };

  return (
    <MapContainer
      center={[-9.645500, -35.734500]}
      zoom={10}
      style={{ height: '60vh', width: '100%', borderRadius: '8px', zIndex: 1 }}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {/* The key forces Leaflet to re-render if geoData changes in the future. */}
      {geoData && <GeoJSON key={JSON.stringify(geoData)} data={geoData} onEachFeature={onEachFeature} />}
    </MapContainer>
  );
}