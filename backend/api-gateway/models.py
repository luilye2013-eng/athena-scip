"""
Athena SCIP - Pydantic v2 Models
Industry-standard response models for API documentation
"""
from datetime import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field, ConfigDict

class StandardResponse(BaseModel):
    """
    Standard API response wrapper.
    All endpoints return this structure for consistency.
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
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
    data: Optional[Any] = Field(
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

class EventResponse(BaseModel):
    """Event data structure"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    description: Optional[str] = None
    event_type: str
    severity: int
    location_country: Optional[str] = None
    location_city: Optional[str] = None
    created_at: str
    confidence_score: Optional[float] = None
    source: Optional[str] = None

class EventsListResponse(BaseModel):
    """Paginated events list response"""
    events: List[EventResponse]
    count: int
    limit: int
    offset: int

class RecommendationResponse(BaseModel):
    """Recommendation data structure"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    action_type: str
    urgency: str
    commodity_id: Optional[str] = None
    supplier_id: Optional[str] = None
    estimated_cost_impact: Optional[float] = None
    event_title: Optional[str] = None
    actions: Optional[List[str]] = None
    affected_commodities: Optional[List[str]] = None

class PriceResponse(BaseModel):
    """Commodity price data structure"""
    commodity_name: str
    price_usd: float
    unit: str
    change_24h: float
    source: str

class CountryRiskResponse(BaseModel):
    """Country risk data structure"""
    country: str
    risk_score: int
    risk_level: str
    events: int
    war: int
    disaster: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database: bool