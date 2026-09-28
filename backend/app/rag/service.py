"""Service RAG principal : orchestration du pipeline complet.

Combine :
- Chargement des documents
- Découpage (chunking)
- Embeddings
- Stockage vectoriel
- Recherche
- Construction du contexte
"""
import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.config import rag_settings
from app.rag.loaders import load_all_documents
from app.rag.chunker import create_chunks
from app.rag.vector_store import get_vector_store
from app.rag.retriever import retrieve_relevant_chunks, build_rag_context, RetrievedChunk

logger = logging.getLogger(__name__)


class RagService:
    """Service principal pour le RAG."""

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialise le service (vérifie la base vectorielle)."""
        if self._initialized:
            return True

        try:
            vector_store = get_vector_store()
            stats = vector_store.get_stats()
            logger.info("RAG Service initialisé - Stats: %s", stats)
            self._initialized = True
            return True
        except Exception as e:
            logger.error("Erreur initialisation RAG Service : %s", e)
            return False

    def ingest_documents(self, paths: Optional[List[str]] = None) -> dict:
        """Pipeline complet d'ingestion des documents.

        Args:
            paths: Chemins optionnels (défaut: config)

        Returns:
            Dict avec statistiques d'ingestion
        """
        logger.info("=== DÉBUT INGESTION RAG ===")

        # 1. Chargement
        logger.info("Étape 1/4: Chargement des documents...")
        path_objects = None
        if paths:
            from pathlib import Path
            path_objects = [Path(p) for p in paths]

        raw_chunks = load_all_documents(path_objects)
        if not raw_chunks:
            return {"success": False, "error": "Aucun document chargé", "chunks_added": 0}

        # 2. Chunking
        logger.info("Étape 2/4: Découpage sémantique...")
        chunks = create_chunks(raw_chunks)
        if not chunks:
            return {"success": False, "error": "Aucun chunk généré", "chunks_added": 0}

        # 3. Embeddings + Stockage
        logger.info("Étape 3/4: Génération embeddings et stockage...")
        vector_store = get_vector_store()
        added = vector_store.add_chunks(chunks)

        # 4. Stats finales
        logger.info("Étape 4/4: Finalisation...")
        stats = vector_store.get_stats()

        result = {
            "success": True,
            "raw_chunks": len(raw_chunks),
            "final_chunks": len(chunks),
            "chunks_added": added,
            "total_in_db": stats["total_chunks"],
            "sources": stats["source_names"],
        }

        logger.info("=== INGESTION TERMINÉE : %s ===", result)
        return result

    def query(
        self,
        question: str,
        top_k: int = None,
        score_threshold: float = None,
    ) -> dict:
        """Effectue une recherche RAG pour une question.

        Args:
            question: Question de l'utilisateur
            top_k: Nombre max de résultats
            score_threshold: Seuil de similarité

        Returns:
            Dict avec chunks, contexte formaté, sources
        """
        if not rag_settings.RAG_ENABLED:
            return {
                "enabled": False,
                "chunks": [],
                "context": "",
                "sources": "",
            }

        chunks = retrieve_relevant_chunks(
            query=question,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        context = build_rag_context(chunks)
        sources = self._format_sources(chunks)

        return {
            "enabled": True,
            "chunks_found": len(chunks),
            "chunks": chunks,
            "context": context,
            "sources": sources,
        }

    def _format_sources(self, chunks: List[RetrievedChunk]) -> str:
        """Formate les sources pour citation."""
        if not chunks:
            return ""

        sources = []
        seen = set()
        for chunk in chunks:
            key = (chunk.source_name, chunk.page_number)
            if key not in seen:
                seen.add(key)
                if chunk.page_number >= 0:
                    sources.append(f"- {chunk.source_name}, page {chunk.page_number}")
                else:
                    sources.append(f"- {chunk.source_name}")

        return "Sources documentaires :\n" + "\n".join(sources)

    def get_stats(self) -> dict:
        """Renvoie les statistiques de la base vectorielle."""
        vector_store = get_vector_store()
        return vector_store.get_stats()

    def reset_database(self) -> bool:
        """Remet à zéro la base vectorielle."""
        vector_store = get_vector_store()
        return vector_store.reset()


# Instance globale
_rag_service: Optional[RagService] = None


def get_rag_service() -> RagService:
    """Renvoie l'instance singleton du service RAG."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RagService()
    return _rag_service