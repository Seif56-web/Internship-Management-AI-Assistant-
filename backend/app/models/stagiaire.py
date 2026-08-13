from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class PeriodeStage(str, enum.Enum):
    ETE = "Été"
    AUTOMNE = "Automne"
    HIVER = "Hiver"
    PFE = "PFE"


class Stagiaire(Base):
    __tablename__ = "stagiaires"

    id = Column(Integer, primary_key=True, index=True)
    nom_complet = Column(String(255), nullable=True, index=True)
    lettre_affectation = Column(Boolean, nullable=True, default=False)
    date_naissance = Column(Date, nullable=True)
    cin = Column(String(8), nullable=True, index=True)
    country_code = Column(String(5), nullable=True, default="+216")
    telephone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    civilite = Column(String(4), nullable=True)
    service = Column(String(255), nullable=True)
    ecole = Column(String(255), nullable=True)
    taille = Column(Integer, nullable=True)
    pointure = Column(Integer, nullable=True)
    date_debut_stage = Column(Date, nullable=True)
    date_fin_stage = Column(Date, nullable=True)
    periode_stage = Column(String(20), nullable=True)
    statut_stage = Column(String(50), default="Stage non débuté", nullable=True)
    statut_dossier = Column(String(50), nullable=True)
    is_extended = Column(Boolean, default=False, nullable=True)
    old_date_fin_stage = Column(Date, nullable=True)
    date_prolongation = Column(DateTime(timezone=True), nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    resumed_at = Column(DateTime(timezone=True), nullable=True)
    encadrant_nom = Column(String(255), nullable=True)
    encadrant_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    encadrant = relationship("User", back_populates="stagiaires", foreign_keys=[encadrant_id])
    rapports = relationship("Rapport", back_populates="stagiaire", cascade="all, delete-orphan")
    validations = relationship("Validation", back_populates="stagiaire", cascade="all, delete-orphan")
    attestations = relationship("Attestation", back_populates="stagiaire", cascade="all, delete-orphan")
    evaluation = relationship("Evaluation", back_populates="stagiaire", uselist=False, cascade="all, delete-orphan")
