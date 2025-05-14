from pydantic import BaseModel
from datetime import datetime

class AtelierCreate(BaseModel):
    bus_id: int
    date_entree: datetime
