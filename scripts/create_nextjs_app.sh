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

# Create the Next.js application with the requested defaults.
echo "=> Creating the Next.js application frontend_demo..."
npx create-next-app@latest frontend_demo --typescript --tailwind --eslint --app

# Enter the generated application directory.
echo "=> Entering the generated application directory..."
cd frontend_demo

# Install the essential map and UI dependencies.
echo "=> Installing essential UI and map dependencies..."
npm install antd @ant-design/nextjs-registry leaflet react-leaflet @types/leaflet reactflow

echo "=> Next.js app setup completed successfully."
