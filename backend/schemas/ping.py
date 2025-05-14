from pydantic import BaseModel

class PingCreate(BaseModel):
    bus_id: int
    status: str
