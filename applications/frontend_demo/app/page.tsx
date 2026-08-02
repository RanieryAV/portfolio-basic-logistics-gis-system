'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Layout, Card, Typography, Spin, message, Row, Col, Button, Statistic } from 'antd';
import ReactFlow, { Background, Controls, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

const { Header, Content } = Layout;
const { Title } = Typography;

// Reads the port from .env (remember that in Next.js client-side, the variable MUST start with NEXT_PUBLIC_)
// We add a fallback ('5557') in case the variable is not found during build.
const API_PORT = process.env.NEXT_PUBLIC_FASTAPI_DATA_PROCESSING_DOCKER || process.env.FASTAPI_DATA_PROCESSING_PORT_DOCKER || '5556';
const API_BASE_URL = `http://localhost:${API_PORT}`;

type GeoData = {
    type: string;
    features: Array<{
        type: string;
        properties: { name: string; [key: string]: any };
        geometry: { type: string; coordinates: any };
    }>;
};

// Dynamic import pointing to the same folder (./Map)
const DynamicMap = dynamic(() => import('./Map'), {
    ssr: false,
    loading: () => <Spin tip="Loading Geographic Engine..." style={{ width: '100%', padding: '50px 0' }} />
});

const initialNodes: Node[] = [
    { id: '1', position: { x: 50, y: 50 }, data: { label: 'PostGIS DB (WKB)' }, type: 'input' },
    { id: '2', position: { x: 50, y: 150 }, data: { label: 'FastAPI (Data Processing)' } },
    { id: '3', position: { x: 50, y: 250 }, data: { label: 'Leaflet UI (GeoJSON)' }, type: 'output' },
];

const initialEdges: Edge[] = [
    { id: 'e1-2', source: '1', target: '2', animated: true },
    { id: 'e2-3', source: '2', target: '3', animated: true },
];

export default function Home() {
    const [apiStatus, setApiStatus] = useState('Checking...');
    const [geoData, setGeoData] = useState<GeoData | null>(null);
    const [neighborhoodData, setNeighborhoodData] = useState<GeoData | null>(null); // New state for Neighborhoods

    const fetchMapData = () => {
        // 1. Fetch Postal Agencies
        fetch(`${API_BASE_URL}/api/v1/collect/get-postal-agencies-from-db`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch map data');
                return res.json();
            })
            .then(data => {
                // Non-destructive fallback: Only update map if DB returned actual features
                if (data && data.features && data.features.length > 0) {
                    setGeoData(data);
                }
            })
            .catch(err => {
                console.error("Could not load map data from DB, keeping fallback.", err);
            });

        // 2. Fetch Neighborhoods
        fetch(`${API_BASE_URL}/api/v1/collect/get-neighborhoods-from-db`)
            .then(res => res.ok ? res.json() : null)
            .then(data => {
                if (data && data.features && data.features.length > 0) {
                    setNeighborhoodData(data);
                }
            })
            .catch(err => console.error("Could not load neighborhoods.", err));
    };

    useEffect(() => {
        // Now using the dynamic base URL constructed with the .env port
        fetch(`${API_BASE_URL}/health`)
            .then((res) => {
                if (!res.ok) throw new Error('Network error');
                return res.json();
            })
            .then((data) => {
                setApiStatus(data.status === 'online' ? 'Online' : 'Offline');
                message.success('Successfully connected to the FastAPI!');
                fetchMapData(); // Fetch the DB data automatically if API is online
            })
            .catch(() => {
                setApiStatus('Offline');
                message.warning('FastAPI is offline. Running fallback data on the map.');
            });

        setGeoData({
            type: 'FeatureCollection',
            features: [
                {
                    type: 'Feature',
                    properties: { name: 'Correios - Superintendência Estadual de Alagoas (SEDE)' },
                    geometry: { type: 'Point', coordinates: [-35.734500, -9.645500] }
                }
            ]
        });
    }, []);

    return (
        <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
            <Header style={{ background: '#001529', padding: '0 20px', display: 'flex', alignItems: 'center' }}>
                <Title level={3} style={{ color: 'white', margin: 0 }}>Logistics GIS DEMO</Title>
            </Header>

            <Content style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
                <Row gutter={[24, 24]}>
                    <Col span={24}>
                        <Card bodyStyle={{ padding: '6px 8px' }}>
                            <Row justify="space-between" align="middle" gutter={[12, 12]}>
                                <Col>
                                    <Statistic
                                        title={`API Status (Port: ${API_PORT})`}
                                        value={apiStatus}
                                        valueStyle={{ fontSize: 16, lineHeight: 1.2 }}
                                    />
                                </Col>
                                <Col>
                                    <Button
                                        type="primary"
                                        onClick={() => {
                                            message.loading({ content: 'Ingesting & Loading All Data...', key: 'ingest' });
                                            
                                            // 1. Trigger the postal agencies ingestion process (reads local file in backend)
                                            const ingestAgencies = fetch(`${API_BASE_URL}/api/v1/collect/ingest-postal-agencies-file`, { method: 'POST' });
                                            
                                            // 2. Fetch Neighborhoods GeoJSON from frontend public folder and POST to backend
                                            const ingestNeighborhoods = fetch(`${API_BASE_URL}/api/v1/collect/ingest-neighborhoods-file`, { method: 'POST' });

                                            // Wait for both ingestions to finish, then fetch the map data
                                            Promise.all([ingestAgencies, ingestNeighborhoods])
                                                .then(async () => {
                                                    message.success({ content: 'Ingestion triggered, loading map data...', key: 'ingest', duration: 3 });
                                                    // Refresh the map with BOTH newly ingested datasets
                                                    fetchMapData(); 
                                                })
                                                .catch(() => {
                                                    message.error({ content: 'Failed to ingest data. Check API logs.', key: 'ingest', duration: 3 });
                                                    // Still attempt to fetch in case data already exists in the DB
                                                    fetchMapData();
                                                });
                                        }}
                                    >
                                        Simulate & Load All Data
                                    </Button>
                                </Col>
                            </Row>
                        </Card>
                    </Col>

                     {/* Spatial Map (Leaflet + PostGIS) - Uses 100% of the screen*/}
                    <Col span={24}>
                        <Card title="Spatial Map (Leaflet + PostGIS)" bordered={false} style={{ height: '100%' }}>
                            {/* Pass both geoData (Agencies) and neighborhoodData (Polygons) to the Map */}
                            <DynamicMap geoData={geoData} neighborhoodData={neighborhoodData} />
                        </Card>
                    </Col>

                    {/* Data Architecture (React Flow) - Uses 100% of the screen and falls to the next line */}
                    <Col span={24}>
                        <Card title="Data Architecture (React Flow)" bordered={false} style={{ height: '100%' }}>
                            <div style={{ height: '400px', width: '100%', border: '1px solid #e8e8e8', borderRadius: '8px' }}>
                                <ReactFlow
                                 defaultNodes={initialNodes} 
                                 defaultEdges={initialEdges} 
                                 fitView 
                                 proOptions={{ hideAttribution: true }}>
                                    <Background color="#e0e0e0" gap={16} />
                                    <Controls />
                                </ReactFlow>
                            </div>
                        </Card>
                    </Col>
                </Row>
            </Content>
        </Layout>
    );
}