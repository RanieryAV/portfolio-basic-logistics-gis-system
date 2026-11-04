'use client';

import React, { useEffect, useRef, useState } from 'react';

// Declaration to prevent TypeScript errors regarding the injected MapLibre and H3 objects
declare global {
  interface Window {
    maplibregl: any;
    h3: any;
  }
}

export type MapProps = {
  geoData: any;
  neighborhoodData?: any;
  streetsData?: any;
  apiPort?: string;
};

export default function Map({ geoData, neighborhoodData, streetsData, apiPort = '5556' }: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const [layers, setLayers] = useState({
    neighborhoods: true,
    streets: true,
    agencies: true,
  });

  // State to track the active base map surface
  const [baseMap, setBaseMap] = useState<'osm' | 'satellite'>('osm');

  // States for H3 Mode ---
  const [isH3Mode, setIsH3Mode] = useState(false);
  
  // MINIMAL CHANGE: Consolidate data into a single state
  const [h3DataMerged, setH3DataMerged] = useState<any>(null);

  // Resolve base API URL dynamically using the port exposed via props
  const API_PORT = apiPort;
  const API_BASE_URL = `http://localhost:${API_PORT}`;

  // --- STATE & HELPER FOR DYNAMIC H3 RESOLUTION ---
  const [h3Resolution, setH3Resolution] = useState<number>(8);
  const gridTimeoutRef = useRef<NodeJS.Timeout | null>(null); // Debounce Ref

  const getH3ResolutionFromZoom = (zoom: number): number => {
    if (zoom <= 5.0) return 1;  // País/Região (Hexágonos massivos, sem sobrecarga)
    if (zoom <= 7.0) return 2;  // Estado (Limpo e esparso)
    if (zoom <= 9.0) return 4;  // Microrregião
    if (zoom <= 11.0) return 5; // Cidade inteira coberta por poucos hexágonos
    if (zoom <= 13.0) return 6; // Regiões da cidade / Conjunto de bairros
    if (zoom <= 14.5) return 7; // Bairro (Hexágonos de ~0.7km², visíveis mas não poluídos)
    if (zoom <= 15.5) return 8; // Sub-bairro / Transição suave
    if (zoom <= 16.5) return 9; // Quarteirões
    return 10;                  // Rua detalhada (intacto, como aprovado por si)
  };

  // --- DYNAMIC BASE GRID GENERATION & RESOLUTION TRACKING ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const updateGridAndResolution = () => {
      // 300ms Debounce to prevent UI freezing on fast scrolls
      if (gridTimeoutRef.current) clearTimeout(gridTimeoutRef.current);
      
      gridTimeoutRef.current = setTimeout(() => {
        const currentZoom = map.getZoom();
        const newResolution = getH3ResolutionFromZoom(currentZoom);
        setH3Resolution((prev) => (prev !== newResolution ? newResolution : prev));

        if (isH3Mode && window.h3) {
          // Generate continuous grid for the current viewport
          const bounds = map.getBounds();
          const nw = bounds.getNorthWest();
          const ne = bounds.getNorthEast();
          const se = bounds.getSouthEast();
          const sw = bounds.getSouthWest();
          
          // GeoJSON polygon representing the screen
          const boundingBox = [[ [nw.lng, nw.lat], [ne.lng, ne.lat], [se.lng, se.lat], [sw.lng, sw.lat], [nw.lng, nw.lat] ]];
          
          try {
            const cells = window.h3.polygonToCells(boundingBox, newResolution, true);

            const features = cells.map((cell: string) => ({
              type: 'Feature',
              geometry: {
                type: 'Polygon',
                coordinates: [window.h3.cellToBoundary(cell, true)]
              },
              properties: { h3_index: cell }
            }));
            
            map.getSource('h3-base-grid').setData({ type: 'FeatureCollection', features });
          } catch (e) {
            console.warn("Viewport too large for H3 grid generation at this resolution.", e);
          }
        }
      }, 300);
    };

    // Update on movement end to render new empty grid areas
    map.on('moveend', updateGridAndResolution);
    
    // Initial call to draw the grid if H3 is activated
    if (isH3Mode) updateGridAndResolution();

    return () => {
      map.off('moveend', updateGridAndResolution);
      if (gridTimeoutRef.current) clearTimeout(gridTimeoutRef.current);
    };
  }, [mapLoaded, isH3Mode]);

  // --- FETCH H3 DATA DYNAMICALLY BASED ON RESOLUTION ---
  useEffect(() => {
    // 1. GARANTIR QUE O H3 SUMA AO SER DESATIVADO
    if (!isH3Mode) {
      setH3DataMerged({ type: 'FeatureCollection', features: [] });
      
      // Limpa a malha de fundo (base grid)
      if (mapRef.current && mapRef.current.getSource('h3-base-grid')) {
        mapRef.current.getSource('h3-base-grid').setData({ type: 'FeatureCollection', features: [] });
      }
      return;
    }

    const fetchH3Data = async () => {
      // 2. ENVIAR REQUISIÇÕES APENAS PARA AS CAMADAS MARCADAS (CHECKED)
      const endpoints: string[] = [];
      if (layers.neighborhoods) endpoints.push(`${API_BASE_URL}/api/v1/collect/get-h3-neighborhoods?resolution=${h3Resolution}`);
      if (layers.streets) endpoints.push(`${API_BASE_URL}/api/v1/collect/get-h3-alagoas-streets?resolution=${h3Resolution}`);
      if (layers.agencies) endpoints.push(`${API_BASE_URL}/api/v1/collect/get-h3-postal-agencies?resolution=${h3Resolution}`);

      // Se H3 estiver ativo mas nenhuma camada selecionada, limpa a exibição
      if (endpoints.length === 0) {
        setH3DataMerged({ type: 'FeatureCollection', features: [] });
        return;
      }

      try {
        const responses = await Promise.all(endpoints.map((url) => fetch(url)));

        const parsedResults = await Promise.all(
          responses.map(async (response) => {
            if (!response.ok) return { type: 'FeatureCollection', features: [] };
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
              return await response.json();
            }
            return { type: 'FeatureCollection', features: [] };
          })
        );

        // Achata todas as features em um único array independentemente de quantas requisições foram feitas
        const mergedFeatures = parsedResults.flatMap(result => result?.features || []);

        setH3DataMerged({
          type: 'FeatureCollection',
          features: mergedFeatures
        });

      } catch (error) {
        console.error('Fatal network/CORS error while fetching H3 datasets:', error);
      }
    };

    fetchH3Data();
    
    // 3. ADICIONAR "layers" ÀS DEPENDÊNCIAS PARA REAGIR AOS CLIQUES DOS CHECKBOXES
  }, [isH3Mode, h3Resolution, layers, API_BASE_URL]);

  // 1. BLIND CDN INJECTION
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initMap = () => {
      if (!mapContainer.current || mapRef.current || !window.maplibregl || !window.h3) return;
      const maplibregl = window.maplibregl;

      const map = new maplibregl.Map({
        container: mapContainer.current,
        maxZoom: 18, 
        style: {
          version: 8,
          sources: {
            'osm-tiles': {
              type: 'raster',
              tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              maxZoom: 18,
              attribution: '&copy; OpenStreetMap contributors'
            },
            'satellite-tiles': {
              type: 'raster',
              tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
              tileSize: 256,
              maxZoom: 18,
              attribution: 'Tiles &copy; Esri'
            }
          },
          layers: [
            {
              id: 'osm-tiles-layer',
              type: 'raster',
              source: 'osm-tiles',
              minzoom: 0,
              maxZoom: 18,
              layout: { visibility: 'visible' }
            },
            {
              id: 'satellite-tiles-layer',
              type: 'raster',
              source: 'satellite-tiles',
              minzoom: 0,
              maxZoom: 18,
              layout: { visibility: 'none' }
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

        // ==========================================
        // ORIGINAL LAYERS
        // ==========================================

        // --- NEIGHBORHOODS ---
        map.addSource('neighborhoods', { type: 'geojson', data: emptyGeoJSON });
        map.addLayer({ id: 'neighborhoods-fill', type: 'fill', source: 'neighborhoods', paint: { 'fill-color': '#1890ff', 'fill-opacity': 0.15 } });
        map.addLayer({ id: 'neighborhoods-line', type: 'line', source: 'neighborhoods', paint: { 'line-color': '#1890ff', 'line-width': 2 } });

        map.on('click', 'neighborhoods-fill', (e: any) => {
          const props = e.features[0].properties;
          // Checking both the DB column format (name, city, state) and the raw file format (NM_BAIRRO, etc.)
          const name = props.name || props.NM_BAIRRO || 'Unknown';
          const city = props.city || props.NM_MUN || 'Unknown';
          const state = props.state || props.NM_UF || 'Unknown';
          const area = props.area_km2 || props.AREA_KM2 || 0;
          
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
        map.addLayer({ id: 'streets-line', type: 'line', source: 'streets', paint: { 'line-color': '#50C878', 'line-width': 2 } });

        map.on('click', 'streets-line', (e: any) => {
          const props = e.features[0].properties;
          // Map matching actual database column names
          const ref = props.ref || 'N/A';
          const postalCod = props.postal_cod || 'N/A';
          const name = props.name || 'Unknown Street';
          const city = props.nm_mun || props.NM_MUN || 'Unknown';
          const neighborhood = props.bairro || props.Bairro || 'Unknown';

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
          const displayState = props.State || props.state || 'AL';

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

        // ==========================================
        // NEW H3 LAYERS
        // ==========================================

        // --- H3 GLOBAL BACKGROUND GRID ---
        map.addSource('h3-base-grid', { type: 'geojson', data: emptyGeoJSON });
        map.addLayer({
          id: 'h3-base-grid-line',
          type: 'line',
          source: 'h3-base-grid',
          paint: { 'line-color': '#8c8c8c', 'line-width': 1, 'line-opacity': 0.3 }
        });

        // Replaced 3 sources with 1 MERGED SOURCE
        map.addSource('h3-merged-data', { type: 'geojson', data: emptyGeoJSON });
        
        // Use Data-Driven Styling based on backend properties.type
        map.addLayer({
          id: 'h3-merged-fill',
          type: 'fill',
          source: 'h3-merged-data',
          paint: {
            'fill-color': [
              'match',
              ['get', 'type'],
              'point_agency', '#ffa39e',
              'polygon_area', '#1890ff',
              'path_line', '#50C878',
              /* default */ '#000000'
            ],
            'fill-opacity': [
              'match',
              ['get', 'type'],
              'point_agency', 0.2,
              'polygon_area', 0.2,
              'path_line', 0.2,
              /* default */ 0.2
            ],
            'fill-outline-color': [
              'match',
              ['get', 'type'],
              'point_agency', '#a8071a',
              'polygon_area', '#0050b3',
              'path_line', '#237841',
              /* default */ '#000000'
            ]
          }
        });

        // Event handling
        map.on('click', 'h3-merged-fill', (e: any) => {
            const props = e.features[0].properties;
            addPopup(e, `
              <div style="font-family: Arial, sans-serif;">
                <h4 style="margin: 0; color: #333;">H3 Cell</h4>
                <p style="margin: 4px 0 2px 0; font-size: 13px;"><strong>Index:</strong> ${props.h3_index}</p>
                <p style="margin: 2px 0; font-size: 13px;"><strong>Ref/Name:</strong> ${props.name || props.ref || 'N/A'}</p>
              </div>
            `);
        });

        // --- POINTER EVENTS (All of the interactive layers) ---
        ['neighborhoods-fill', 'streets-line', 'agencies-point', 'h3-merged-fill'].forEach(layer => {
          map.on('mouseenter', layer, () => { map.getCanvas().style.cursor = 'pointer'; });
          map.on('mouseleave', layer, () => { map.getCanvas().style.cursor = ''; });
        });

        setMapLoaded(true);
        setTimeout(() => map.resize(), 150);
      });
    };

    const loadScripts = async () => {
      if (!window.maplibregl) {
        await new Promise((resolve) => {
          const script = document.createElement('script');
          script.src = 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js';
          script.onload = resolve;
          document.head.appendChild(script);
        });
      }
      if (!window.h3) {
        await new Promise((resolve) => {
          const script = document.createElement('script');
          script.src = 'https://unpkg.com/h3-js@4.1.0/dist/h3-js.umd.js';
          script.onload = resolve;
          document.head.appendChild(script);
        });
      }
      initMap();
    };

    if (window.maplibregl && window.h3) {
      initMap();
    } else {
      if (!document.getElementById('maplibre-css')) {
        const link = document.createElement('link');
        link.id = 'maplibre-css';
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css';
        document.head.appendChild(link);
      }
      loadScripts();
    }
  }, []);

  // 2. DATA INJECTION
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    try {
      // Injects originals
      if (neighborhoodData?.features) map.getSource('neighborhoods').setData(neighborhoodData);
      if (geoData?.features) map.getSource('agencies').setData(geoData);
      if (streetsData?.features) map.getSource('streets').setData(streetsData);

      // MINIMAL CHANGE: Inject merged GeoJSON
      if (h3DataMerged?.features) map.getSource('h3-merged-data').setData(h3DataMerged);
      
    } catch (error) {
      console.error('Error injecting data:', error);
    }
  }, [mapLoaded, geoData, neighborhoodData, streetsData, h3DataMerged]);

  // 3. VECTOR LAYER VISIBILITY CONTROL
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const setVisibility = (layerId: string, isVisible: boolean) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', isVisible ? 'visible' : 'none');
      }
    };

    // Original layers (they appear if the layer is ON and the H3 is OFF)
    setVisibility('neighborhoods-fill', layers.neighborhoods && !isH3Mode);
    setVisibility('neighborhoods-line', layers.neighborhoods && !isH3Mode);
    setVisibility('streets-line', layers.streets && !isH3Mode);
    setVisibility('agencies-point', layers.agencies && !isH3Mode);

  }, [layers, isH3Mode, mapLoaded, h3Resolution]);

  // 4. BASE MAP VISIBILITY CONTROL
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    if (baseMap === 'osm') {
      map.setLayoutProperty('osm-tiles-layer', 'visibility', 'visible');
      map.setLayoutProperty('satellite-tiles-layer', 'visibility', 'none');
    } else {
      map.setLayoutProperty('osm-tiles-layer', 'visibility', 'none');
      map.setLayoutProperty('satellite-tiles-layer', 'visibility', 'visible');
    }
  }, [baseMap, mapLoaded]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '450px' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%', minHeight: '450px', borderRadius: '8px', zIndex: 1 }} />

      {/* BASE MAP CONTROL MENU */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        background: 'rgba(255, 255, 255, 0.95)',
        padding: '12px',
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        zIndex: 2,
        fontFamily: 'Arial, sans-serif'
      }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#333' }}>Base Map</h4>

        <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', cursor: 'pointer' }}>
          <input 
            type="radio" 
            name="basemap" 
            value="osm" 
            checked={baseMap === 'osm'} 
            onChange={() => setBaseMap('osm')} 
            style={{ marginRight: '8px' }}
          />
          OpenStreetMap
        </label>

        <label style={{ display: 'block', fontSize: '13px', cursor: 'pointer' }}>
          <input 
            type="radio" 
            name="basemap" 
            value="satellite" 
            checked={baseMap === 'satellite'} 
            onChange={() => setBaseMap('satellite')} 
            style={{ marginRight: '8px' }}
          />
          Satellite Imagery (ArcGIS)
        </label>
      </div>

      {/* VECTOR LAYERS CONTROL MENU */}
      <div style={{
        position: 'absolute', top: '10px', right: '10px',
        background: 'rgba(255, 255, 255, 0.95)', padding: '12px', borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)', zIndex: 2, fontFamily: 'Arial, sans-serif', width: '220px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', paddingBottom: '10px', borderBottom: '1px solid #ddd' }}>
          <h4 style={{ margin: 0, fontSize: '14px', color: '#333' }}>Layers Control</h4>
          
          {/* TOGGLE H3 BUTTON */}
          <label style={{ fontSize: '12px', fontWeight: 'bold', cursor: 'pointer', background: isH3Mode ? '#e6f7ff' : '#f5f5f5', border: `1px solid ${isH3Mode ? '#91d5ff' : '#d9d9d9'}`, padding: '4px 8px', borderRadius: '4px', color: isH3Mode ? '#0050b3' : '#595959' }}>
            <input type="checkbox" checked={isH3Mode} onChange={e => setIsH3Mode(e.target.checked)} style={{ display: 'none' }} />
            {isH3Mode ? 'H3 Active' : 'H3 Inactive'}
          </label>
        </div>

        <label style={{ display: 'flex', alignItems: 'center', marginBottom: '6px', fontSize: '13px', cursor: 'pointer' }}>
          <input type="checkbox" checked={layers.neighborhoods} onChange={e => setLayers(prev => ({...prev, neighborhoods: e.target.checked}))} style={{ marginRight: '8px' }}/>
          <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#1890ff', marginRight: '6px', borderRadius: '2px', border: '1px solid #ccc' }}></span>
          Neighborhoods (MultiPolygon)
        </label>

        <label style={{ display: 'flex', alignItems: 'center', marginBottom: '6px', fontSize: '13px', cursor: 'pointer' }}>
          <input type="checkbox" checked={layers.streets} onChange={e => setLayers(prev => ({...prev, streets: e.target.checked}))} style={{ marginRight: '8px' }}/>
          <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#50C878', marginRight: '6px', borderRadius: '2px', border: '1px solid #ccc' }}></span>
          Alagoas Streets (MultiLineString)
        </label>

        <label style={{ display: 'flex', alignItems: 'center', fontSize: '13px', cursor: 'pointer' }}>
          <input type="checkbox" checked={layers.agencies} onChange={e => setLayers(prev => ({...prev, agencies: e.target.checked}))} style={{ marginRight: '8px' }}/>
          <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#f5222d', marginRight: '6px', borderRadius: '2px', border: '1px solid #ccc' }}></span>
          Postal Agencies (Point)
        </label>
      </div>
    </div>
  );
}