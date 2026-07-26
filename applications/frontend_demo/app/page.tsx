'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Layout, Card, Typography, Spin, message, Row, Col, Button, Statistic } from 'antd';
import ReactFlow, { Background, Controls, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

const { Header, Content } = Layout;
const { Title } = Typography;

type GeoData = {
    type: string;
    features: Array<{
        type: string;
        properties: { name: string };
        geometry: { type: string; coordinates: number[] };
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

    useEffect(() => {
        fetch('http://localhost:5000/health')
            .then((res) => {
                if (!res.ok) throw new Error('Network error');
                return res.json();
            })
            .then((data) => {
                setApiStatus(data.status === 'online' ? 'Online' : 'Offline');
                message.success('Successfully connected to the FastAPI!');
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
                                        title="API Status (Data Processing)"
                                        value={apiStatus}
                                        valueStyle={{ fontSize: 16, lineHeight: 1.2 }}
                                    />
                                </Col>
                                <Col>
                                    <Button
                                        type="primary"
                                        onClick={() => message.info('Trajectory ingestion (WKT) via POST will be enabled soon.')}
                                    >
                                        Simulate Trajectory Ingestion
                                    </Button>
                                </Col>
                            </Row>
                        </Card>
                    </Col>

                     {/* Spatial Map (Leaflet + PostGIS) - Uses 100% of the screen*/}
                    <Col span={24}>
                        <Card title="Spatial Map (Leaflet + PostGIS)" bordered={false} style={{ height: '100%' }}>
                            <DynamicMap geoData={geoData} />
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