"""
Athena SCIP - Pydantic v2 Models
Industry-standard response models for API documentation
"""
from datetime import datetime
from typing import Optional, List, Dict, Union
from pydantic import BaseModel, Field, ConfigDict

class StandardResponse(BaseModel):
    """
    Standard API response wrapper.
    All endpoints return this structure for consistency.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=False,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {"message": "Operation successful"},
                "error": None,
                "timestamp": "2026-01-01T00:00:00.000Z"
            }
        }
    )
    
    success: bool = Field(
        default=True,
        description="Indicates if the operation was successful"
    )
    data: Optional[Union[dict, list, str, int, float, bool]] = Field(
        default=None,
        description="The response data payload"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if success is False"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp of the response"
    )