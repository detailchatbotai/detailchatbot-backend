from pydantic import BaseModel, ConfigDict
from typing import Dict

class ShopRead(BaseModel):
    id: str
    name: str
    services: Dict[str, float]
    booking_link: str

    model_config = ConfigDict(from_attributes=True)
