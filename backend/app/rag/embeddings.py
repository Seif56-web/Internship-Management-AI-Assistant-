"""Génération d'embeddings locaux via sentence-transformers.

Utilise un modèle multilingue pour supporter le français.
"""
import logging
from typing import List, Optional, TYPE_CHECKING

import numpy as np

from app.rag.config import rag_settings
from app.rag.loaders import DocumentChunk

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Cache global du modèle
_embedding_model: Optional["SentenceTransformer"] = None


def get_embedding_model() -> "SentenceTransformer":
    """Charge et met en cache le modèle d'embedding.

    L'import de `sentence_transformers` est fait ici (et non au niveau du
    module) pour que le simple fait d'importer `app.rag.embeddings` ne
    fasse pas planter le processus si le paquet n'est pas installé ou si
    son chargement (ou celui du modèle) échoue. L'appelant (handle_rag_query)
    intercepte l'exception et renvoie une réponse dégradée au lieu d'un
    HTTP 500.
    """
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RuntimeError(
                "Le paquet 'sentence-transformers' n'est pas installé : "
                "le module RAG (recherche documentaire) est indisponible."
            ) from e
        logger.info("Chargement du modèle d'embedding : %s", rag_settings.RAG_EMBEDDING_MODEL)
        _embedding_model = SentenceTransformer(rag_settings.RAG_EMBEDDING_MODEL)
        logger.info("Modèle d'embedding chargé (dimension=%d)", _embedding_model.get_sentence_embedding_dimension())
    return _embedding_model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Génère les embeddings pour une liste de textes."""
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    return embeddings.tolist()


def embed_text(text: str) -> List[float]:
    """Génère l'embedding pour un texte unique."""
    return embed_texts([text])[0]


def embed_chunks(chunks: List[DocumentChunk]) -> List[List[float]]:
    """Génère les embeddings pour une liste de chunks de documents."""
    texts = [chunk.content for chunk in chunks]
    return embed_texts(texts)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calcule la similarité cosinus entre deux vecteurs."""
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))


def get_embedding_dimension() -> int:
    """Renvoie la dimension des embeddings du modèle configuré."""
    return get_embedding_model().get_sentence_embedding_dimension()