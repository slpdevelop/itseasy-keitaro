from pydantic import BaseModel, ConfigDict


class Base(BaseModel):
    """Base model"""

    model_config = ConfigDict(from_attributes=True)
