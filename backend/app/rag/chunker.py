"""Découpage sémantique des documents en chunks pour le RAG.

Stratégie :
- Découpage par paragraphes avec chevauchement
- Taille cible configurable (RAG_CHUNK_SIZE)
- Chevauchement configurable (RAG_CHUNK_OVERLAP)
- Préservation des métadonnées du document source
"""
import logging
import re
from typing import List

from app.rag.loaders import DocumentChunk
from app.rag.config import rag_settings

logger = logging.getLogger(__name__)


def split_into_paragraphs(text: str) -> List[str]:
    """Divise un texte en paragraphes non vides."""
    # Normaliser les sauts de ligne
    text = re.sub(r"\r\n?", "\n", text)
    # Diviser par double saut de ligne ou plus
    paragraphs = re.split(r"\n\s*\n", text)
    # Filtrer et nettoyer
    return [p.strip() for p in paragraphs if p.strip()]


def create_chunks(
    raw_chunks: List[DocumentChunk],
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[DocumentChunk]:
    """Découpe les chunks bruts en chunks sémantiques de taille contrôlée.

    Args:
        raw_chunks: Chunks bruts issus du chargement (par page/section)
        chunk_size: Taille cible en caractères (défaut: config)
        chunk_overlap: Chevauchement en caractères (défaut: config)

    Returns:
        Liste de DocumentChunk découpés sémantiquement
    """
    if chunk_size is None:
        chunk_size = rag_settings.RAG_CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = rag_settings.RAG_CHUNK_OVERLAP

    final_chunks = []
    global_chunk_index = 0

    for raw_chunk in raw_chunks:
        paragraphs = split_into_paragraphs(raw_chunk.content)

        if not paragraphs:
            continue

        # Si le texte est déjà assez petit, le garder tel quel
        if len(raw_chunk.content) <= chunk_size:
            new_chunk = DocumentChunk(
                content=raw_chunk.content,
                source_path=raw_chunk.source_path,
                chunk_index=global_chunk_index,
                page_number=raw_chunk.page_number,
                document_type=raw_chunk.document_type,
            )
            final_chunks.append(new_chunk)
            global_chunk_index += 1
            continue

        # Sinon, construire des chunks par accumulation de paragraphes
        current_chunk_paragraphs = []
        current_length = 0

        for para in paragraphs:
            para_len = len(para)

            # Si un seul paragraphe dépasse la taille cible, le découper
            if para_len > chunk_size:
                # Vider le chunk actuel s'il y a du contenu
                if current_chunk_paragraphs:
                    chunk_text = "\n\n".join(current_chunk_paragraphs)
                    new_chunk = DocumentChunk(
                        content=chunk_text,
                        source_path=raw_chunk.source_path,
                        chunk_index=global_chunk_index,
                        page_number=raw_chunk.page_number,
                        document_type=raw_chunk.document_type,
                    )
                    final_chunks.append(new_chunk)
                    global_chunk_index += 1
                    current_chunk_paragraphs = []
                    current_length = 0

                # Découper le long paragraphe en sous-chunks
                sub_chunks = _split_long_text(para, chunk_size, chunk_overlap)
                for sub_chunk in sub_chunks:
                    new_chunk = DocumentChunk(
                        content=sub_chunk,
                        source_path=raw_chunk.source_path,
                        chunk_index=global_chunk_index,
                        page_number=raw_chunk.page_number,
                        document_type=raw_chunk.document_type,
                    )
                    final_chunks.append(new_chunk)
                    global_chunk_index += 1
                continue

            # Vérifier si l'ajout dépasse la taille cible
            if current_length + para_len > chunk_size and current_chunk_paragraphs:
                # Finaliser le chunk actuel
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                new_chunk = DocumentChunk(
                    content=chunk_text,
                    source_path=raw_chunk.source_path,
                    chunk_index=global_chunk_index,
                    page_number=raw_chunk.page_number,
                    document_type=raw_chunk.document_type,
                )
                final_chunks.append(new_chunk)
                global_chunk_index += 1

                # Garder le chevauchement : reprendre les derniers paragraphes
                overlap_paragraphs = _get_overlap_paragraphs(
                    current_chunk_paragraphs, chunk_overlap
                )
                current_chunk_paragraphs = overlap_paragraphs
                current_length = sum(len(p) for p in overlap_paragraphs) + 2 * len(overlap_paragraphs)

            current_chunk_paragraphs.append(para)
            current_length += para_len + 2  # +2 pour les "\n\n"

        # Dernier chunk
        if current_chunk_paragraphs:
            chunk_text = "\n\n".join(current_chunk_paragraphs)
            new_chunk = DocumentChunk(
                content=chunk_text,
                source_path=raw_chunk.source_path,
                chunk_index=global_chunk_index,
                page_number=raw_chunk.page_number,
                document_type=raw_chunk.document_type,
            )
            final_chunks.append(new_chunk)
            global_chunk_index += 1

    logger.info("Découpage terminé : %d chunk(s) final(s) (taille cible=%d, overlap=%d)",
                len(final_chunks), chunk_size, chunk_overlap)
    return final_chunks


def _split_long_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Découpe un texte long en chunks avec chevauchement.

    Essaie de couper aux phrases, sinon aux mots, sinon aux caractères.
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Si on n'est pas à la fin, chercher un bon point de coupure
        if end < text_len:
            # Chercher une fin de phrase
            sentence_end = text.rfind(". ", start, end)
            if sentence_end == -1:
                sentence_end = text.rfind(".\n", start, end)
            if sentence_end != -1:
                end = sentence_end + 1
            else:
                # Chercher un espace
                space_pos = text.rfind(" ", start, end)
                if space_pos != -1:
                    end = space_pos

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Avancer avec chevauchement
        start = max(start + 1, end - chunk_overlap)

    return chunks


def _get_overlap_paragraphs(paragraphs: List[str], overlap_chars: int) -> List[str]:
    """Récupère les derniers paragraphes pour atteindre le chevauchement cible."""
    if not paragraphs:
        return []

    overlap_paragraphs = []
    total_len = 0

    for para in reversed(paragraphs):
        overlap_paragraphs.insert(0, para)
        total_len += len(para) + 2
        if total_len >= overlap_chars:
            break

    return overlap_paragraphs