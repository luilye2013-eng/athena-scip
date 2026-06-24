"""
Athena SCIP - Pydantic Models for Request/Response Validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime

# ============================================
# Request Models
# ============================================

class EventFilter(BaseModel):
    """Filter parameters for events endpoint"""
    event_type: Optional[str] = Field(None, description="Filter by event type")
    min_severity: Optional[int] = Field(None, ge=1, le=5, description="Minimum severity (1-5)")
    limit: int = Field(100, ge=1, le=500, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Pagination offset")
    
    @field_validator('event_type')
    def validate_event_type(cls, v):
        if v is not None:
            valid_types = ['war', 'natural_disaster', 'strike', 'sanctions', 'pandemic', 'other', 'all']
            if v not in valid_types:
                raise ValueError(f'event_type must be one of: {valid_types}')
        return v

class RecommendationRequest(BaseModel):
    """Request model for generating recommendations"""
    event_id: str
    organization_id: str
    action_type: str = "mitigation"

class PriceAlert(BaseModel):
    """Request model for price alerts"""
    commodity_name: str
    threshold_percent: float = Field(5.0, ge=1, le=50, description="Alert threshold in percent")

# ============================================
# Response Models
# ============================================

class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"message": "Operation successful"},
                "timestamp": "2026-01-01T00:00:00.000Z"
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: bool
    timestamp: str

# ============================================
# Error Models
# ============================================

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    code: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
