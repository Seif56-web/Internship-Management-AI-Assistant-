from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Encadrant(Base):
    __tablename__ = "encadrants"

    id = Column(Integer, primary_key=True, index=True)
    code_encadrant = Column(String(10), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)

    user = relationship("User")
