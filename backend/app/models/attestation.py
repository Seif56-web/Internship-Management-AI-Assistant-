from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Attestation(Base):
    __tablename__ = "attestations"

    id = Column(Integer, primary_key=True, index=True)
    stagiaire_id = Column(Integer, ForeignKey("stagiaires.id"), nullable=False)
    numero_attestation = Column(String(50), unique=True, nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    pdf_url = Column(String(512), nullable=True)
    data_snapshot = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stagiaire = relationship("Stagiaire", back_populates="attestations")
