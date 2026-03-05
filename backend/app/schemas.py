from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models import ClimbStatus


class ClimbResponse(BaseModel):
    id: int
    video_url: str
    status: ClimbStatus
    # Keep it as a generic Dictionary to allow flexible JSON
    analysis_results: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
