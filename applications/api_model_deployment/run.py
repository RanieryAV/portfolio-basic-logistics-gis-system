import os
import subprocess
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

FASTAPI_MODEL_DEPLOYMENT_HOST = os.getenv("FASTAPI_MODEL_DEPLOYMENT_HOST")
FASTAPI_MODEL_DEPLOYMENT_PORT = int(os.getenv("FASTAPI_MODEL_DEPLOYMENT_PORT"))

# Initializing FastAPI at module import time so ASGI servers can discover `app`
app = FastAPI(
	title="Logistics GIS API - Model Deployment",
	description="API for inferring and deploying the previously trained Machine Learning models",
	version="1.0"
)

# Setting up CORS to allow for front-end requests (Next.js on port 3000)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"], # In prod replace for ["http://localhost:3000"]
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Here the refactored controllers will be imported and included later on
# from applications.api_data_processing.src.controllers.process_data_controller import router
# app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health_check():
	return {"status": "online", "api": "Model Deployment", "framework": "FastAPI"}

if __name__ == "__main__":
	# Used mainly if this is executed directly from 'python run.py' (ex: inside Docker)
	uvicorn.run(app, host=FASTAPI_MODEL_DEPLOYMENT_HOST, port=FASTAPI_MODEL_DEPLOYMENT_PORT)
