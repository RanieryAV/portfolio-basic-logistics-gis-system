'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Layout, Card, Typography, Spin, message, Row, Col, Button } from 'antd';
import ReactFlow, { Background, Controls, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

const { Header, Content } = Layout;
const { Title } = Typography;

const DynamicMap = dynamic(() => import('./Map'), {
    ssr: false,
    loading: () => <Spin description="Loading Geographic Engine..." style={{ width: '100%', padding: '50px 0' }} />
});

export default function Home() {
    const [apiPort, setApiPort] = useState('5556');
    const [apiStatus, setApiStatus] = useState('Checking...');
    const [geoData, setGeoData] = useState<any>(null);
    const [neighborhoodData, setNeighborhoodData] = useState<any>(null);
    const [streetsData, setStreetsData] = useState<any>(null);

    const API_BASE_URL = `http://localhost:${apiPort}`;

    const fetchMapData = (activePort: string) => {
        const baseUrl = `http://localhost:${activePort}`;

        fetch(`${baseUrl}/api/v1/collect/get-postal-agencies-from-db`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch map data');
                return res.json();
            })
            .then(data => {
                if (data && data.features && data.features.length > 0) setGeoData(data);
            })
            .catch(err => console.error("Could not load map data from DB, keeping fallback.", err));

        fetch(`${baseUrl}/api/v1/collect/get-neighborhoods-from-db`)
            .then(res => res.ok ? res.json() : null)
            .then(data => {
                if (data && data.features && data.features.length > 0) setNeighborhoodData(data);
            })
            .catch(err => console.error("Could not load neighborhoods.", err));
            
        fetch(`${baseUrl}/api/v1/collect/get-alagoas-streets-from-db`)
            .then(res => res.ok ? res.json() : null)
            .then(data => {
                if (data && data.features && data.features.length > 0) setStreetsData(data);
            })
            .catch(err => console.error("Could not load streets.", err));
    };

    useEffect(() => {
        const checkPortsAndConnect = async () => {
            const portsToTest = ['5556', '5557'];
            let connected = false;

            for (const port of portsToTest) {
                try {
                    const res = await fetch(`http://localhost:${port}/health`);
                    if (res.ok) {
                        const data = await res.json();
                        setApiPort(port);
                        setApiStatus(data.status === 'online' ? 'Online' : 'Offline');
                        message.success(`Successfully connected to FastAPI on port ${port}!`);
                        fetchMapData(port);
                        connected = true;
                        break;
                    }
                } catch (err) {
                    console.warn(`Port ${port} is offline, trying next...`);
                }
            }

            if (!connected) {
                setApiStatus('Offline');
                message.warning('FastAPI is offline. Running fallback data on the map.');
            }
        };

        checkPortsAndConnect();

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
        <Layout style={{ height: '100vh', background: '#f0f2f5', overflow: 'hidden' }}>
            <Header style={{ background: '#001529', padding: '0 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Title level={3} style={{ color: 'white', margin: 0 }}>GIS Prototype</Title>
                
                {/* Elements moved to the right side of the Header */}
                <Row align="middle" gutter={16}>
                    <Col>
                        <span style={{ color: 'rgba(255, 255, 255, 0.65)', marginRight: 8, fontSize: '14px' }}>
                            API Status (Port: {apiPort}):
                        </span>
                        <span style={{ color: apiStatus === 'Online' ? '#52c41a' : '#ff4d4f', fontWeight: 'bold', fontSize: '14px' }}>
                            {apiStatus}
                        </span>
                    </Col>
                    <Col>
                        <Button
                            type="primary"
                            onClick={() => {
                                message.loading({ content: 'Ingesting & Loading All Data...', key: 'ingest' });
                                
                                const ingestAgencies = fetch(`${API_BASE_URL}/api/v1/collect/ingest-postal-agencies-file`, { method: 'POST' });
                                const ingestNeighborhoods = fetch(`${API_BASE_URL}/api/v1/collect/ingest-neighborhoods-file`, { method: 'POST' });
                                const ingestStreets = fetch(`${API_BASE_URL}/api/v1/collect/ingest-alagoas-streets-file`, { method: 'POST' });

                                Promise.all([ingestAgencies, ingestNeighborhoods, ingestStreets])
                                    .then(async () => {
                                        message.success({ content: 'Ingestion triggered, loading map data...', key: 'ingest', duration: 3 });
                                        fetchMapData(apiPort); 
                                    })
                                    .catch(() => {
                                        message.error({ content: 'Failed to ingest data. Check API logs.', key: 'ingest', duration: 3 });
                                        fetchMapData(apiPort);
                                    });
                            }}
                        >
                            Simulate & Load All Data
                        </Button>
                    </Col>
                </Row>
            </Header>

            <Content style={{ padding: '12px', width: '100%', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '12px' }}>
                    
                    <Card 
                        title="Spatial Map (MapLibre + PostGIS)" 
                        variant="borderless" 
                        style={{ display: 'flex', flexDirection: 'column', flex: 1 }} 
                        styles={{ body: { flex: 1, padding: 0 } }}
                    >
                        <DynamicMap apiPort={apiPort} geoData={geoData} neighborhoodData={neighborhoodData} streetsData={streetsData} />
                    </Card>
                </div>
            </Content>
        </Layout>
    );
}