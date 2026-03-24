"""
Quarts de travail pour le personnel de guichet (agents, gestionnaires).
Référence : normes de base Canada (pauses, durée max) — voir docs/CANADA_NORMES.md.
Les chauffeurs sont planifiés via les départs (table departs), pas via ce modèle.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Time, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class StaffShift(Base):
    __tablename__ = "staff_shifts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    work_date = Column(DateTime, nullable=False, index=True)  # date (heure minuit UTC stockée)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    timezone = Column(String, nullable=False, default="America/Toronto")
    break_minutes = Column(Integer, default=0)  # pause non rémunérée déclarée (ex. 30 min Ontario si >5h)
    notes = Column(String, nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="staff_shifts")

    def __repr__(self):
        return f"<StaffShift user={self.user_id} {self.work_date}>"
