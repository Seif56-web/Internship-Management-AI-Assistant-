"""Configuration RAG (Retrieval-Augmented Generation).

Centralise tous les paramètres RAG via les variables d'environnement.
"""
from pathlib import Path
from typing import List

from app.config import settings


class RagSettings:
    """Wrapper pour accéder aux settings RAG depuis la config principale."""

    # Activation
    RAG_ENABLED: bool = settings.RAG_ENABLED

    # Recherche
    RAG_TOP_K: int = settings.RAG_TOP_K
    RAG_SCORE_THRESHOLD: float = settings.RAG_SCORE_THRESHOLD

    # Chunking
    RAG_CHUNK_SIZE: int = settings.RAG_CHUNK_SIZE
    RAG_CHUNK_OVERLAP: int = settings.RAG_CHUNK_OVERLAP

    # Stockage vectoriel
    RAG_VECTOR_DB_PATH: str = settings.RAG_VECTOR_DB_PATH

    # Modèle d'embedding (local via sentence-transformers)
    RAG_EMBEDDING_MODEL: str = settings.RAG_EMBEDDING_MODEL

    # Chemins des documents à indexer (séparés par des virgules)
    RAG_DOCUMENT_PATHS: str = settings.RAG_DOCUMENT_PATHS

    def get_document_paths(self) -> List[Path]:
        """Renvoie la liste des chemins de documents à indexer."""
        paths = []
        for p in self.RAG_DOCUMENT_PATHS.split(","):
            p = p.strip()
            if p:
                path = Path(p)
                if path.exists():
                    if path.is_dir():
                        paths.append(path)
                    elif path.is_file():
                        paths.append(path)
                    else:
                        paths.append(path)
                else:
                    # Chemin qui n'existe pas encore, on l'ajoute quand même
                    paths.append(Path(p))
        return paths


rag_settings = RagSettings()