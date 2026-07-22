import os
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Import routers
from src.controllers import collect_data_controller
from src.controllers import process_data_controller

# Load environment variables
load_dotenv()

FASTAPI_DATA_PROCESSING_HOST = os.getenv("FASTAPI_DATA_PROCESSING_HOST")
FASTAPI_DATA_PROCESSING_PORT = int(os.getenv("FASTAPI_DATA_PROCESSING_PORT"))

if __name__ == "__main__":
    # Initializing FastAPI
	app = FastAPI(
		title="Logistics GIS API - Data Processing",
		description="API for ingesting and processing WKT/WKB geometries",
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
	
	# Import and include the refactored controllers
	app.include_router(collect_data_controller.router, prefix="/api/v1")
	app.include_router(process_data_controller.router, prefix="/api/v1")
	
	@app.get("/health")
	def health_check():
		return {"status": "online", "api": "Data Processing", "framework": "FastAPI"}
	
	if __name__ == "__main__":
		# Used mainly if this is executed directly from 'python run.py' (ex: inside Docker)
		uvicorn.run(app, host=FASTAPI_DATA_PROCESSING_HOST, port=FASTAPI_DATA_PROCESSING_PORT)
