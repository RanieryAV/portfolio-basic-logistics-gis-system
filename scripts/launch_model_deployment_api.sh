#!/bin/bash

# Add the root directory to the PYTHONPATH
export PYTHONPATH=$(pwd)

# activate the virtual environment
VENV_NAME="logistics_gis_venv"
source "./$VENV_NAME/bin/activate"
source "./$VENV_NAME/Scripts/activate"

echo "="
echo " Initializing Local API: Model Deployment (FastAPI)"
echo "="

echo "=> Activating virtual environment..."
source logistics_gis_venv/bin/activate

echo "=> Initializing Uvicorn with Hot-Reload on port 5002..."

# Run the API
uvicorn applications.api_model_deployment.run:app --host 0.0.0.0 --port 5002 --reload
