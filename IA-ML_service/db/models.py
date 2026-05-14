from numpy import positive
from alembic.util.sqla_compat import AUTOINCREMENT_DEFAULT
from sqlalchemy import (
    Column, String, Text, Float, Integer,
    DateTime, Date, func, ForeignKey,Boolean
)
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base
from sqlalchemy import LargeBinary

class Potential_linkedin(Base):
    __tablename__ = "potential_linkedin"
    identifiant = Column(Integer, primary_key=True, autoincrement=True)
    posts = Column(JSONB, nullable=True)
    potential_score = Column(Integer, nullable=True)
    positive_signals = Column(JSONB, nullable=True)
    negative_signals = Column(JSONB, nullable=True)
    needs_it = Column(JSONB, nullable=True)
    recommandation = Column(String, nullable=True)
    emailsgenerated = Column(JSONB, nullable=True)
    identifiantEntreprise = Column(String, nullable=True)

    

    
    