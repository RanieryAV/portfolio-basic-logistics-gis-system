
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# IMPORT THE SERVICES
from src.services.collect_data_service import (
    IngestPostalAgenciesService,
    QueryPostalAgenciesService,
)

# Router replacing the 'Namespace' from flask_restx
router = APIRouter(prefix="/collect", tags=["Data Collection"])

# ---------------------------------------------------------
# Pydantic Schemas (Replacing the @api.model from Flask-RestX)
# ---------------------------------------------------------
class GeoDataPayload(BaseModel):
    """Validation model for the input of geographical data"""
    source_name: str = Field(..., description="Name of the data source (ex: 'truck_fleet')")
    wkt_geometry: str = Field(..., description="Geometry in WKT format (Well-Known Text)")
    timestamp: str | None = Field(None, description="Date and time of the data collection ISO 8601")

# ---------------------------------------------------------
# Controller Class
# ---------------------------------------------------------
class CollectDataController:
    """
    Controller class to manage endpoints related to data collection.
    """

    async def collect_raw_data(self, payload: GeoDataPayload):
        """
        Receives a payload containing WKT geometries and forwards them to the service layer.
        The validation of fields is automatically done by Pydantic.
        """
        try:
            # Example of how you would evoke the service:
            # service = CollectDataService()
            # result = service.collect_raw_data(source=payload.source_name, wkt=payload.wkt_geometry)
            
            return {
                "status": "success", 
                "message": "Geographical data collected and queued successfully.",
                "received_data": payload.model_dump() # Converts the Pydantic object to dict
            }
        except ValueError as ve:
            # Validation or business errors
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception:
            # Generic server errors
            raise HTTPException(status_code=500, detail="Internal error during data collection.")

    async def ingest_postal_agencies(self):
        """
        Instantiates the service that reads the local dataset 'correios_al.geojson.json' 
        and performs an UPSERT of all agencies into the PostalAgencies table in PostGIS.
        """
        try:
            # Instantiating the class and executing its functionality
            ingest_service = IngestPostalAgenciesService()
            result = ingest_service.execute()
            
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_postal_agencies_from_db(self):
        """
        Fetches all postal agencies from the PostGIS database and returns them as a GeoJSON FeatureCollection.
        """
        try:
            query_service = QueryPostalAgenciesService()
            result = query_service.execute()
            return result
        except Exception:
            # Return empty FeatureCollection to gracefully handle failures (non-destructive)
            return {"type": "FeatureCollection", "features": []}

# ---------------------------------------------------------
# Router Mappings
# ---------------------------------------------------------
# Instantiating the Controller
controller_instance = CollectDataController()

# Binding the instance methods to the FastAPI router
router.add_api_route(
    "/", 
    controller_instance.collect_raw_data, 
    methods=["POST"], 
    summary="Collect raw geographical data"
)

router.add_api_route(
    "/ingest-postal-agencies-file", 
    controller_instance.ingest_postal_agencies, 
    methods=["POST"], 
    summary="Ingest Postal Agencies GeoJSON"
)

router.add_api_route(
    "/get-postal-agencies-from-db", 
    controller_instance.get_postal_agencies_from_db, 
    methods=["GET"], 
    summary="Get Postal Agencies as GeoJSON"
)