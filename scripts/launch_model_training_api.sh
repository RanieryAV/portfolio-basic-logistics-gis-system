#!/bin/bash

# Add the root directory to the PYTHONPATH
export PYTHONPATH=$(pwd)

# Load environment variables from the repository .env file
set -a
source ./.env
set +a

# activate the virtual environment
VENV_NAME="logistics_gis_venv"
source "./$VENV_NAME/bin/activate"
source "./$VENV_NAME/Scripts/activate"

echo "="
echo " Initializing Local API: Model Training (FastAPI)"
echo "="

echo "=> Activating virtual environment..."
source logistics_gis_venv/bin/activate

echo "=> Initializing Uvicorn with Hot-Reload on port ${FASTAPI_MODEL_TRAINING_PORT}..."

# Run the API
uvicorn applications.api_model_training.run:app --host 0.0.0.0 --port ${FASTAPI_MODEL_TRAINING_PORT} --reload
