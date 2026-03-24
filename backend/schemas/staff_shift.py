from pydantic import BaseModel, Field
from datetime import datetime, time
from typing import Optional


class StaffShiftCreate(BaseModel):
    user_id: int
    work_date: datetime  # date du quart
    start_time: str  # "HH:MM"
    end_time: str
    timezone: str = "America/Toronto"
    break_minutes: int = 0
    notes: Optional[str] = None


class StaffShiftUpdate(BaseModel):
    work_date: Optional[datetime] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    break_minutes: Optional[int] = None
    notes: Optional[str] = None


class StaffShiftOut(BaseModel):
    id: int
    user_id: int
    work_date: datetime
    start_time: str
    end_time: str
    timezone: str
    break_minutes: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True
