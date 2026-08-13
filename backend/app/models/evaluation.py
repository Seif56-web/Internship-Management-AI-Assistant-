from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    stagiaire_id = Column(Integer, ForeignKey("stagiaires.id"), nullable=False)
    encadrant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    qualite_travail = Column(Integer, nullable=True)
    autonomie = Column(Integer, nullable=True)
    ponctualite = Column(Integer, nullable=True)
    communication = Column(Integer, nullable=True)
    esprit_equipe = Column(Integer, nullable=True)
    capacite_apprentissage = Column(Integer, nullable=True)
    initiative = Column(Integer, nullable=True)
    respect_consignes = Column(Integer, nullable=True)
    recommandation_embauche = Column(String(20), nullable=True)
    commentaire = Column(Text, nullable=True)
    date_creation = Column(DateTime(timezone=True), server_default=func.now())
    date_modification = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("qualite_travail IS NULL OR (qualite_travail >= 1 AND qualite_travail <= 5)", name="ck_qualite_travail"),
        CheckConstraint("autonomie IS NULL OR (autonomie >= 1 AND autonomie <= 5)", name="ck_autonomie"),
        CheckConstraint("ponctualite IS NULL OR (ponctualite >= 1 AND ponctualite <= 5)", name="ck_ponctualite"),
        CheckConstraint("communication IS NULL OR (communication >= 1 AND communication <= 5)", name="ck_communication"),
        CheckConstraint("esprit_equipe IS NULL OR (esprit_equipe >= 1 AND esprit_equipe <= 5)", name="ck_esprit_equipe"),
        CheckConstraint("capacite_apprentissage IS NULL OR (capacite_apprentissage >= 1 AND capacite_apprentissage <= 5)", name="ck_capacite_apprentissage"),
        CheckConstraint("initiative IS NULL OR (initiative >= 1 AND initiative <= 5)", name="ck_initiative"),
        CheckConstraint("respect_consignes IS NULL OR (respect_consignes >= 1 AND respect_consignes <= 5)", name="ck_respect_consignes"),
        CheckConstraint("recommandation_embauche IS NULL OR recommandation_embauche IN ('oui', 'non', 'a_considerer')", name="ck_recommandation_embauche"),
    )

    stagiaire = relationship("Stagiaire", back_populates="evaluation")
    encadrant = relationship("User")
