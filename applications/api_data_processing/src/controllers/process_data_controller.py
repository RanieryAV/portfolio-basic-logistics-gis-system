from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Router replacing the 'Namespace' from flask_restx
router = APIRouter(prefix="/process", tags=["Data Processing"])

# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------
class ProcessRequestPayload(BaseModel):
    """Validation model for the input of processing request"""
    target_table: str = Field(..., description="Name of the target PostGIS table")
    apply_smoothing: bool = Field(default=False, description="Apply smoothing over the WKT trajectory?")

# ---------------------------------------------------------
# Controller Class
# ---------------------------------------------------------
class ProcessDataController:
    """
    Controller class to manage endpoints related to data processing.
    """

    async def process_spatial_data(self, payload: ProcessRequestPayload):
        """
        Actives the geographical data conversion/processing pipeline (WKT to WKB, etc).
        """
        try:
            # Example of how you would evoke the service:
            # process_data_service.execute(payload.target_table, payload.apply_smoothing)
            
            return {
                "status": "success",
                "message": f"Processing started for the table = {payload.target_table}"
            }
        except ValueError as ve:
            # Validation or business errors
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            # Generic server errors
            raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# Router Mappings
# ---------------------------------------------------------
# Instantiating the Controller
controller_instance = ProcessDataController()

# Binding the instance methods to the FastAPI router
router.add_api_route(
    "/", 
    controller_instance.process_spatial_data, 
    methods=["POST"], 
    summary="Process stored geometries"
)