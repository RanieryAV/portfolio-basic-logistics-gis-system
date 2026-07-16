#!/bin/bash

# Export envs from .env if needed
export $(grep -v '^#' /app/.env | xargs || true)

# Data processing specific env vars
PROCESSED_OUTPUT_DIR=${PROCESSED_OUTPUT_DIR}

# Debug logs
echo "Running as user: $(id)"

exec "$@"
