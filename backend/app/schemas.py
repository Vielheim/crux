from pydantic import BaseModel, ConfigDict
from app.models import ClimbStatus


class ClimbResponse(BaseModel):
    id: int
    video_url: str
    status: ClimbStatus

    # This config tells Pydantic to read data even if it's not a dict
    # (e.g. it can read from a SQLAlchemy object)
    model_config = ConfigDict(from_attributes=True)
