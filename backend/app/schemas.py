from pydantic import BaseModel, ConfigDict
from app.models import ClimbStatus
from typing import Optional, List, Dict, Any


class ClimbResponse(BaseModel):
    id: int
    video_url: str
    status: ClimbStatus
    pose_data: Optional[List[Dict[str, Any]]] = None  # Add this line!

    # This config tells Pydantic to read data even if it's not a dict
    # (e.g. it can read from a SQLAlchemy object)
    model_config = ConfigDict(from_attributes=True)
