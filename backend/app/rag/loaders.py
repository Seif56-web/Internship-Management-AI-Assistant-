"""Chargeurs de documents pour le pipeline RAG.

Supporte :
- PDF (pypdf)
- DOCX (python-docx)
- TXT (natif)
"""
import logging
from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader
from docx import Document as DocxDocument

from app.rag.config import rag_settings

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


class DocumentChunk:
    """Représente un morceau de document avec ses métadonnées."""

    def __init__(
        self,
        content: str,
        source_path: Path,
        chunk_index: int,
        page_number: Optional[int] = None,
        document_type: Optional[str] = None,
    ):
        self.content = content
        self.source_path = source_path
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.document_type = document_type or source_path.suffix.lower().lstrip(".")

    @property
    def metadata(self) -> dict:
        """Métadonnées pour le stockage vectoriel."""
        return {
            "source": str(self.source_path),
            "source_name": self.source_path.name,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number if self.page_number is not None else -1,
            "document_type": self.document_type,
        }

    def __repr__(self) -> str:
        return f"DocumentChunk(source={self.source_path.name}, chunk={self.chunk_index}, len={len(self.content)})"


def load_text_file(path: Path) -> str:
    """Charge un fichier texte."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def load_pdf_file(path: Path) -> List[tuple[str, int]]:
    """Charge un PDF et renvoie une liste de (texte, page_number)."""
    try:
        reader = PdfReader(str(path))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append((text, i + 1))
        return pages
    except Exception as e:
        logger.error("Erreur lecture PDF %s : %s", path, e)
        return []


def load_docx_file(path: Path) -> str:
    """Charge un fichier DOCX."""
    try:
        doc = DocxDocument(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        logger.error("Erreur lecture DOCX %s : %s", path, e)
        return ""


def load_document(path: Path) -> List[tuple[str, Optional[int]]]:
    """Charge un document selon son extension.

    Renvoie une liste de (texte, page_number).
    Pour les formats sans pages (txt, docx), page_number = None.
    """
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf_file(path)
    elif suffix == ".docx":
        text = load_docx_file(path)
        return [(text, None)] if text else []
    elif suffix == ".txt":
        text = load_text_file(path)
        return [(text, None)] if text else []
    else:
        logger.warning("Format non supporté : %s", path)
        return []


def discover_documents(paths: Optional[List[Path]] = None) -> List[Path]:
    """Découvre récursivement tous les documents supportés."""
    if paths is None:
        paths = rag_settings.get_document_paths()

    documents = []
    for path in paths:
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            documents.append(path)
        elif path.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                documents.extend(path.rglob(f"*{ext}"))
        else:
            logger.warning("Chemin ignoré (n'existe pas) : %s", path)

    # Dédupliquer et trier
    unique_docs = sorted(set(documents))
    logger.info("%d document(s) découvert(s)", len(unique_docs))
    return unique_docs


def load_all_documents(paths: Optional[List[Path]] = None) -> List[DocumentChunk]:
    """Charge tous les documents et les découpe en chunks bruts (sans chunking sémantique)."""
    documents = discover_documents(paths)
    all_chunks = []

    for doc_path in documents:
        try:
            pages = load_document(doc_path)
            if not pages:
                logger.warning("Document vide ou illisible : %s", doc_path)
                continue

            # Pour l'instant, on garde les pages comme chunks bruts
            # Le chunking sémantique sera fait dans chunker.py
            for page_num, (text, page_number) in enumerate(pages):
                if text.strip():
                    chunk = DocumentChunk(
                        content=text.strip(),
                        source_path=doc_path,
                        chunk_index=page_num,
                        page_number=page_number,
                    )
                    all_chunks.append(chunk)

        except Exception as e:
            logger.error("Erreur chargement %s : %s", doc_path, e)

    logger.info("%d chunk(s) brut(s) chargé(s)", len(all_chunks))
    return all_chunks