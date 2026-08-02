'use client';

import { useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, LayersControl } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default function Map({ geoData, neighborhoodData }: { geoData: any , neighborhoodData?: any }) {
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

  const onEachNeighborhood = (feature: any, layer: L.Layer) => {
    if (feature.properties) {
      const name = feature.properties.NM_BAIRRO || 'Unknown';
      const city = feature.properties.NM_MUN || 'Unknown';
      const state = feature.properties.NM_UF || 'Unknown';
      const area = feature.properties.AREA_KM2 || 0;
      layer.bindPopup(`
        <div style="font-family: Arial, sans-serif;">
          <h4 style="margin: 0; color: #1890ff;">${name}</h4>
          <p style="margin: 4px 0 2px 0; font-size: 13px;"><strong>City/State:</strong> ${city} - ${state}</p>
          <p style="margin: 2px 0; font-size: 13px;"><strong>Area:</strong> ${Number(area).toFixed(2)} km²</p>
        </div>
      `);
    }
  };

  return (
    <MapContainer
      center={[-9.645500, -35.734500]}
      zoom={10}
      style={{ height: '60vh', width: '100%', borderRadius: '8px', zIndex: 1 }}
    >
      <LayersControl position="topright">
        {/* Base Layer: The actual map background */}
        <LayersControl.BaseLayer checked name="OpenStreetMap">
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        </LayersControl.BaseLayer>

        {/* Overlay: Neighborhood Polygons */}
        {neighborhoodData && (
          <LayersControl.Overlay checked name="Neighborhoods (Polygons)">
            <GeoJSON 
               key={`neigh-${JSON.stringify(neighborhoodData).substring(0,20)}`} 
               data={neighborhoodData} 
               onEachFeature={onEachNeighborhood}
               style={{ color: '#1890ff', weight: 2, fillOpacity: 0.15 }}
            />
          </LayersControl.Overlay>
        )}

        
        {/* Overlay: The togglable points from PostGIS */}
        {geoData && (
          <LayersControl.Overlay checked name="Postal Agencies (PostGIS)">
            <GeoJSON key={JSON.stringify(geoData)} data={geoData} onEachFeature={onEachFeature} />
          </LayersControl.Overlay>
        )}
      </LayersControl>
    </MapContainer>
  );
}