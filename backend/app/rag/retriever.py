"""Récupérateur RAG : recherche sémantique et construction du contexte."""
import logging
from typing import List, Optional

from app.rag.config import rag_settings
from app.rag.embeddings import embed_text
from app.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class RetrievedChunk:
    """Chunk récupéré avec score de similarité."""

    def __init__(
        self,
        content: str,
        source_name: str,
        source_path: str,
        page_number: int,
        document_type: str,
        chunk_index: int,
        similarity: float,
    ):
        self.content = content
        self.source_name = source_name
        self.source_path = source_path
        self.page_number = page_number
        self.document_type = document_type
        self.chunk_index = chunk_index
        self.similarity = similarity

    @property
    def citation(self) -> str:
        """Citation formatée pour l'affichage."""
        parts = [f"Source: {self.source_name}"]
        if self.page_number >= 0:
            parts.append(f"page {self.page_number}")
        parts.append(f"(score: {self.similarity:.2f})")
        return " | ".join(parts)

    def __repr__(self) -> str:
        return f"RetrievedChunk({self.source_name}, p.{self.page_number}, sim={self.similarity:.2f})"


def retrieve_relevant_chunks(
    query: str,
    top_k: int = None,
    score_threshold: float = None,
) -> List[RetrievedChunk]:
    """Recherche les chunks pertinents pour une requête.

    Args:
        query: Question de l'utilisateur
        top_k: Nombre max de résultats
        score_threshold: Seuil de similarité minimum

    Returns:
        Liste de RetrievedChunk triés par pertinence
    """
    if not rag_settings.RAG_ENABLED:
        logger.debug("RAG désactivé")
        return []

    if not query or not query.strip():
        return []

    try:
        # Générer l'embedding de la requête
        query_embedding = embed_text(query)

        # Recherche vectorielle
        vector_store = get_vector_store()
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        # Convertir en objets RetrievedChunk
        retrieved = []
        for r in results:
            meta = r["metadata"]
            chunk = RetrievedChunk(
                content=r["document"],
                source_name=meta.get("source_name", "inconnu"),
                source_path=meta.get("source", "inconnu"),
                page_number=meta.get("page_number", -1),
                document_type=meta.get("document_type", "inconnu"),
                chunk_index=meta.get("chunk_index", -1),
                similarity=r["similarity"],
            )
            retrieved.append(chunk)

        logger.info("RAG retrieval: %d chunk(s) pertinent(s) pour '%s...'",
                    len(retrieved), query[:50])
        return retrieved

    except Exception as e:
        logger.error("Erreur retrieval RAG : %s", e)
        return []


def build_rag_context(retrieved_chunks: List[RetrievedChunk], max_chars: int = 4000) -> str:
    """Construit un contexte formaté à partir des chunks récupérés.

    Args:
        retrieved_chunks: Chunks récupérés
        max_chars: Taille max du contexte en caractères

    Returns:
        Contexte formaté pour le LLM
    """
    if not retrieved_chunks:
        return ""

    context_parts = ["=== CONTEXTE DOCUMENTAIRE (RAG) ==="]
    current_length = len(context_parts[0])

    for i, chunk in enumerate(retrieved_chunks, 1):
        chunk_text = f"\n--- Document {i} ---\n"
        chunk_text += f"Source: {chunk.source_name}"
        if chunk.page_number >= 0:
            chunk_text += f" (page {chunk.page_number})"
        chunk_text += f"\n{chunk.content}\n"

        if current_length + len(chunk_text) > max_chars:
            # Tronquer le dernier chunk si nécessaire
            remaining = max_chars - current_length - 50
            if remaining > 100:
                chunk_text = chunk_text[:remaining] + "\n[tronqué...]\n"
                context_parts.append(chunk_text)
            break

        context_parts.append(chunk_text)
        current_length += len(chunk_text)

    context_parts.append("\n=== FIN CONTEXTE DOCUMENTAIRE ===")
    return "\n".join(context_parts)


def format_sources(retrieved_chunks: List[RetrievedChunk]) -> str:
    """Formate la liste des sources pour citation."""
    if not retrieved_chunks:
        return ""

    sources = []
    seen = set()
    for chunk in retrieved_chunks:
        key = (chunk.source_name, chunk.page_number)
        if key not in seen:
            seen.add(key)
            if chunk.page_number >= 0:
                sources.append(f"- {chunk.source_name}, page {chunk.page_number}")
            else:
                sources.append(f"- {chunk.source_name}")

    return "Sources documentaires :\n" + "\n".join(sources)