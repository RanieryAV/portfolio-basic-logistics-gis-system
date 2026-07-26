from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

# Router replaces the 'Namespace' from flask_restx
router = APIRouter(prefix="/collect", tags=["Data Collection"])

# ---------------------------------------------------------
# Pydantic Schemas (replaces the @api.model from Flask-RestX)
# ---------------------------------------------------------
class GeoDataPayload(BaseModel):
    """Validation model for the input of geographical data"""
    source_name: str = Field(..., description="Name of the data sources (ex: 'ship_fleet')")
    wkt_geometry: str = Field(..., description="Geometry in WKT format (Well-Known Text)")
    timestamp: Optional[str] = Field(None, description="Date and time of the data collection ISO 8601")

# ---------------------------------------------------------
# Endpoints (replaces 'Resource' classes from Flask-RestX)
# ---------------------------------------------------------
@router.post("/", summary="Colect raw geographical data")
async def collect_raw_data(payload: GeoDataPayload):
    """
    Receives a payload containing WKT geometries and forwards them to the service layer.
    The validation of fields is automatically done by Pydantic.
    """
    try:
        # Example of how you would evoke a service (import it at the top of the file):
        # result = collect_data_service.execute(
        #     source=payload.source_name, 
        #     wkt=payload.wkt_geometry
        # )
        
        return {
            "status": "success", 
            "message": "Geographical data colected sucessfully.",
            "received_data": payload.model_dump() # Converts the Pydantic object to dict
        }
    except ValueError as ve:
        # Validation or business errors
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Generic server errors
        raise HTTPException(status_code=500, detail="Internal error during data collection.")
