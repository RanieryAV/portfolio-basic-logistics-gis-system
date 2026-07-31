#!/bin/bash

# Add the root directory to the PYTHONPATH (Maintained for monorepo consistency)
export PYTHONPATH=$(pwd)

# Load environment variables from the repository .env file
set -a
source ./.env
set +a

echo "="
echo " Initializing Local App: Frontend Demo (Next.js)"
echo "="

echo "=> Navigating to frontend directory..."
cd applications/frontend_demo

# Check if the 'next' binary actually exists
if [ ! -f "node_modules/.bin/next" ]; then
    echo "=> Local dependencies missing or incomplete."
    
    # If the directory exists but lacks the binary, it is a Docker ghost folder.
    if [ -d "node_modules" ]; then
        echo "=> Cleaning up broken or root-owned node_modules..."
        sudo rm -rf node_modules
    fi
    
    echo "=> Installing dependencies locally..."
    npm install
fi

# Clear .next cache if it is locked by root
if [ -d ".next" ] && [ ! -w ".next" ]; then
    echo "=> Fixing locked or root-owned .next cache..."
    sudo rm -rf .next
fi

echo "=> Initializing Next.js with Hot-Reload on port ${FRONTEND_DEMO_PORT}..."

# Run the frontend application
PORT=${FRONTEND_DEMO_PORT} npm run dev