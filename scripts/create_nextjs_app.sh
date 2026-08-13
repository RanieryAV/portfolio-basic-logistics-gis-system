#!/usr/bin/env bash
set -euo pipefail

# Resolve the repository root from the location of this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Check the minimal prerequisites before continuing.
command -v npx >/dev/null 2>&1 || { echo "Error: npx is not installed or not available in PATH." >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "Error: npm is not installed or not available in PATH." >&2; exit 1; }
[[ -d "${REPO_ROOT}/applications" ]] || { echo "Error: applications directory not found at ${REPO_ROOT}/applications." >&2; exit 1; }

# Move to the applications directory before creating the Next.js app.
echo "=> Changing to applications directory..."
cd "${REPO_ROOT}/applications"

# Remove a pasta antiga se existir para garantir uma instalação limpa
if [[ -d "frontend_demo" ]]; then
    echo "=> Removing existing frontend_demo directory..."
    rm -rf frontend_demo
fi

# Create the Next.js application with the requested defaults.
echo "=> Creating the Next.js application frontend_demo..."
npx --yes create-next-app@latest frontend_demo --typescript --tailwind --eslint --app

# Enter the generated application directory.
echo "=> Entering the generated application directory..."
cd frontend_demo

# Install the essential map and UI dependencies.
echo "=> Installing essential UI and map dependencies..."
npm install antd @ant-design/nextjs-registry maplibre-gl react-map-gl reactflow --legacy-peer-deps

# Configura o Turbopack root para evitar que ele busque dependências na raiz do repositório
echo "=> Writing next.config.ts with explicit turbopack root..."
cat << 'EOF' > next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
EOF

echo "=> Next.js app setup completed successfully."