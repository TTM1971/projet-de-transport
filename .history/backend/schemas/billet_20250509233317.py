from pydantic import BaseModel
from datetime import datetime

class BilletCreate(BaseModel):
    bus_id: int
    destination_id: int
    siege: int
    agent_id: int
    mode_paiement: str

class Billet(BilletCreate):
    id: int
    date_achat: datetime = datetime.now()
