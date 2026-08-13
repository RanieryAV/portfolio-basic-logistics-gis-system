'use client';

import React, { useEffect, useRef, useState } from 'react';

// Declaration to prevent TypeScript errors regarding the injected MapLibre object
declare global {
  interface Window {
    maplibregl: any;
  }
}

export type MapProps = {
  geoData: any;
  neighborhoodData?: any;
  streetsData?: any;
};

export default function Map({ geoData, neighborhoodData, streetsData }: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const [layers, setLayers] = useState({
    neighborhoods: true,
    streets: true,
    agencies: true,
  });

  // 1. BLIND CDN INJECTION
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initMap = () => {
      if (!mapContainer.current || mapRef.current || !window.maplibregl) return;
      const maplibregl = window.maplibregl;

      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: {
          version: 8,
          sources: {
            'osm-tiles': {
              type: 'raster',
              tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              attribution: '&copy; OpenStreetMap contributors'
            }
          },
          layers: [
            {
              id: 'osm-tiles-layer',
              type: 'raster',
              source: 'osm-tiles',
              minzoom: 0,
              maxzoom: 19
            }
          ]
        },
        center: [-35.734500, -9.645500],
        zoom: 10,
      });

      map.addControl(new maplibregl.NavigationControl(), 'bottom-right');
      mapRef.current = map;

      map.on('load', () => {
        console.log('Native MapLibre loaded via CDN successfully.');
        const emptyGeoJSON = { type: 'FeatureCollection', features: [] };

        const addPopup = (e: any, html: string) => {
          if (!e.features?.[0]) return;
          new maplibregl.Popup({ offset: 15 }).setLngLat(e.lngLat).setHTML(html).addTo(map);
        };

        // --- NEIGHBORHOODS ---
        map.addSource('neighborhoods', { type: 'geojson', data: emptyGeoJSON });
        map.addLayer({ id: 'neighborhoods-fill', type: 'fill', source: 'neighborhoods', paint: { 'fill-color': '#1890ff', 'fill-opacity': 0.15 } });
        map.addLayer({ id: 'neighborhoods-line', type: 'line', source: 'neighborhoods', paint: { 'line-color': '#1890ff', 'line-width': 2 } });

        map.on('click', 'neighborhoods-fill', (e: any) => {
          const props = e.features[0].properties;
          const name = props.NM_BAIRRO || 'Unknown';
          const city = props.NM_MUN || 'Unknown';
          const state = props.NM_UF || 'Unknown';
          const area = props.AREA_KM2 || 0;
          
          addPopup(e, `
            <div style="font-family: Arial, sans-serif;">
              <h4 style="margin: 0; color: #1890ff;">${name}</h4>
              <p style="margin: 4px 0 2px 0; font-size: 13px;"><strong>City/State:</strong> ${city} - ${state}</p>
              <p style="margin: 2px 0; font-size: 13px;"><strong>Area:</strong> ${Number(area).toFixed(2)} km²</p>
            </div>
          `);
        });

        // --- STREETS ---
        map.addSource('streets', { type: 'geojson', data: emptyGeoJSON });
        map.addLayer({ id: 'streets-line', type: 'line', source: 'streets', paint: { 'line-color': '#8c8c8c', 'line-width': 1 } });

        map.on('click', 'streets-line', (e: any) => {
          const props = e.features[0].properties;
          const ref = props.ref || 'N/A';
          const postalCod = props.postal_cod || 'N/A';
          const name = props.name || 'Unknown Street';
          const city = props.NM_MUN || 'Unknown';
          const neighborhood = props.Bairro || 'Unknown';

          addPopup(e, `
            <div style="font-family: Arial, sans-serif; min-width: 200px;">
              <h4 style="margin: 0; color: #595959;">${name}</h4>
              <p style="margin: 4px 0 2px 0; font-size: 13px;"><strong>Reference:</strong> ${ref}</p>
              <p style="margin: 2px 0; font-size: 13px;"><strong>Postal Code:</strong> ${postalCod}</p>
              <p style="margin: 2px 0; font-size: 13px;"><strong>City:</strong> ${city}</p>
              <p style="margin: 2px 0; font-size: 13px;"><strong>Neighborhood:</strong> ${neighborhood}</p>
            </div>
          `);
        });

        // --- POSTAL AGENCIES (Native Circle) ---
        map.addSource('agencies', { type: 'geojson', data: emptyGeoJSON });
        map.addLayer({
          id: 'agencies-point',
          type: 'circle',
          source: 'agencies',
          paint: {
            'circle-radius': 7,
            'circle-color': '#f5222d',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff'
          }
        });

        map.on('click', 'agencies-point', (e: any) => {
          const props = e.features[0].properties;
          const displayName = props.Name || props.Nome || 'Unknown Agency';
          const displayAddress = props.Address || props.Endereço || 'N/A';
          const displayCity = props.City || props.Cidade || 'N/A';
          const displayZip = props['ZIP Code'] || props.CEP || 'N/A';
          const displayPhone = props.Phone || props.Telefone || 'N/A';
          const displayState = props.state || 'AL';

          addPopup(e, `
            <div style="font-family: Arial, sans-serif; min-width: 200px;">
              <h4 style="margin-top: 0; margin-bottom: 8px; color: #001529;">${displayName}</h4>
              <p style="margin: 4px 0; font-size: 13px;"><strong>Address:</strong> ${displayAddress}</p>
              <p style="margin: 4px 0; font-size: 13px;"><strong>City:</strong> ${displayCity} - ${displayState}</p>
              <p style="margin: 4px 0; font-size: 13px;"><strong>ZIP Code:</strong> ${displayZip}</p>
              <p style="margin: 4px 0; font-size: 13px;"><strong>Phone:</strong> ${displayPhone}</p>
            </div>
          `);
        });

        // --- POINTER EVENTS (All interactive layers) ---
        ['neighborhoods-fill', 'streets-line', 'agencies-point'].forEach(layer => {
          map.on('mouseenter', layer, () => { map.getCanvas().style.cursor = 'pointer'; });
          map.on('mouseleave', layer, () => { map.getCanvas().style.cursor = ''; });
        });

        setMapLoaded(true);
        setTimeout(() => map.resize(), 150);
      });
    };

    if (window.maplibregl) {
      initMap();
    } else {
      if (!document.getElementById('maplibre-css')) {
        const link = document.createElement('link');
        link.id = 'maplibre-css';
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css';
        document.head.appendChild(link);
      }
      if (!document.getElementById('maplibre-js')) {
        const script = document.createElement('script');
        script.id = 'maplibre-js';
        script.src = 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js';
        script.onload = initMap;
        document.head.appendChild(script);
      }
    }
  }, []);

  // 2. DATA INJECTION
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    try {
      if (neighborhoodData?.features) {
        map.getSource('neighborhoods').setData(neighborhoodData);
      }

      if (geoData?.features) {
        map.getSource('agencies').setData(geoData);
      }

      if (streetsData?.features) {
        map.getSource('streets').setData(streetsData);
      }
    } catch (error) {
      console.error('Error injecting data:', error);
    }
  }, [mapLoaded, geoData, neighborhoodData, streetsData]);

  // 3. LAYER VISIBILITY CONTROL
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const setVisibility = (layerId: string, isVisible: boolean) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', isVisible ? 'visible' : 'none');
      }
    };

    setVisibility('neighborhoods-fill', layers.neighborhoods);
    setVisibility('neighborhoods-line', layers.neighborhoods);
    setVisibility('streets-line', layers.streets);
    setVisibility('agencies-point', layers.agencies);
  }, [layers, mapLoaded]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '60vh', minHeight: '450px' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%', minHeight: '450px', borderRadius: '8px', zIndex: 1 }} />

      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        background: 'rgba(255, 255, 255, 0.95)',
        padding: '12px',
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: 2,
        fontFamily: 'Arial, sans-serif'
      }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#333' }}>Layers Control</h4>

        <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', cursor: 'pointer' }}>
          <input type="checkbox" checked={layers.neighborhoods} onChange={e => setLayers(prev => ({...prev, neighborhoods: e.target.checked}))} style={{ marginRight: '8px' }}/>
          Neighborhoods (MultiPolygon)
        </label>

        <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', cursor: 'pointer' }}>
          <input type="checkbox" checked={layers.streets} onChange={e => setLayers(prev => ({...prev, streets: e.target.checked}))} style={{ marginRight: '8px' }}/>
          Alagoas Streets (MultiLineString)
        </label>

        <label style={{ display: 'block', fontSize: '13px', cursor: 'pointer' }}>
          <input type="checkbox" checked={layers.agencies} onChange={e => setLayers(prev => ({...prev, agencies: e.target.checked}))} style={{ marginRight: '8px' }}/>
          Postal Agencies (Point)
        </label>
      </div>
    </div>
  );
}