import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  turbopack: {
    root: process.cwd(),
  },
  // Allow the Docker IP so Hot-Reload (HMR) and dynamic component loading (such as the map) work without being blocked.
    allowedDevOrigins: [
        '172.18.0.11',
        '172.19.0.11',
        '172.18.0.12',
        '172.19.0.12',
        '192.168.0.8',
        'localhost'
    ]
};

export default nextConfig;
