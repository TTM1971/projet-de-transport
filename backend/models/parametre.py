from sqlalchemy import Column, Integer, String, Text, Boolean
from database import Base

class Parametre(Base):
    __tablename__ = "parametres"
    
    id = Column(Integer, primary_key=True, index=True)
    cle = Column(String, unique=True, nullable=False, index=True)
    valeur = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # string, integer, float, boolean, json
    description = Column(Text)
    categorie = Column(String, index=True)  # tarifs, taxes, systeme, etc.
    is_modifiable = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Parametre {self.cle}={self.valeur}>"
