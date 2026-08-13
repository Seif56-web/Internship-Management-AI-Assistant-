from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class StatutValidation(str, enum.Enum):
    VALIDE = "valide"
    REFUSE = "refuse"
    SUSPENDU = "suspendu"


class Validation(Base):
    __tablename__ = "validations"

    id = Column(Integer, primary_key=True, index=True)
    stagiaire_id = Column(Integer, ForeignKey("stagiaires.id"), nullable=False)
    encadrant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SAEnum(StatutValidation, values_callable=lambda x: [e.value for e in x]), nullable=False)
    commentaire = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stagiaire = relationship("Stagiaire", back_populates="validations")
    encadrant = relationship("User", back_populates="validations")
