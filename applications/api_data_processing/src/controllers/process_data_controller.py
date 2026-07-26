from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/process", tags=["Data Processing"])

class ProcessRequestPayload(BaseModel):
    target_table: str = Field(..., description="Name of the target PostGIS table")
    apply_smoothing: bool = Field(default=False, description="Apply smoothing over the WKT trajectory?")

@router.post("/", summary="Process stored geometries")
async def process_spatial_data(payload: ProcessRequestPayload):
    """
    Actives the geographical data conversion/processing pipeline (WKT to WKB, etc).
    """
    try:
        # process_data_service.execute(payload.target_table, payload.apply_smoothing)
        
        return {
            "status": "success",
            "message": f"Processing started for the table = {payload.target_table}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
