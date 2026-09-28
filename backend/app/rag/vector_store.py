"""Stockage vectoriel avec FAISS pour le RAG.

Persistance locale (index + métadonnées), ajout/recherche/suppression de documents.
"""
import logging
import json
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING

import numpy as np

from app.rag.config import rag_settings
from app.rag.loaders import DocumentChunk
from app.rag.embeddings import embed_chunks, get_embedding_dimension

if TYPE_CHECKING:
    import faiss

logger = logging.getLogger(__name__)


def _import_faiss():
    """Import paresseux de faiss : évite qu'un `import app.rag.vector_store`
    ne plante si `faiss-cpu` n'est pas installé (l'erreur ne remonte alors
    qu'au moment où le vector store est réellement utilisé, et est capturée
    par handle_rag_query)."""
    try:
        import faiss
        return faiss
    except ImportError as e:
        raise RuntimeError(
            "Le paquet 'faiss-cpu' n'est pas installé : "
            "le module RAG (recherche documentaire) est indisponible."
        ) from e

INDEX_FILE = "faiss_index.bin"
METADATA_FILE = "faiss_metadata.json"
CHUNK_DATA_FILE = "faiss_chunks.pkl"


class VectorStore:
    """Wrapper autour de FAISS pour le stockage des embeddings."""

    def __init__(self, persist_path: Optional[str] = None):
        self._faiss = _import_faiss()
        self.persist_path = Path(persist_path or rag_settings.RAG_VECTOR_DB_PATH)
        self.persist_path.mkdir(parents=True, exist_ok=True)

        self._index: Optional["faiss.Index"] = None
        self._metadata: List[Dict[str, Any]] = []
        self._chunk_data: List[DocumentChunk] = []
        self._dimension = get_embedding_dimension()
        self._id_to_idx: Dict[str, int] = {}

        # Charger l'index existant si disponible
        self._load()

    def _get_index_path(self) -> Path:
        return self.persist_path / INDEX_FILE

    def _get_metadata_path(self) -> Path:
        return self.persist_path / METADATA_FILE

    def _get_chunk_data_path(self) -> Path:
        return self.persist_path / CHUNK_DATA_FILE

    def _load(self) -> bool:
        """Charge l'index FAISS et les métadonnées depuis le disque."""
        index_path = self._get_index_path()
        metadata_path = self._get_metadata_path()
        chunk_data_path = self._get_chunk_data_path()

        if index_path.exists() and metadata_path.exists():
            try:
                self._index = self._faiss.read_index(str(index_path))
                with open(metadata_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
                with open(chunk_data_path, "rb") as f:
                    self._chunk_data = pickle.load(f)

                # Reconstruire le mapping id -> idx
                self._id_to_idx = {meta["id"]: i for i, meta in enumerate(self._metadata)}

                logger.info("FAISS index chargé : %d vecteurs (dim=%d)", self._index.ntotal, self._dimension)
                return True
            except Exception as e:
                logger.warning("Impossible de charger l'index existant : %s", e)
                self._init_empty_index()
        else:
            self._init_empty_index()
        return False

    def _init_empty_index(self):
        """Initialise un index FAISS vide."""
        # IndexIVFFlat pour la recherche par similarité cosinus
        # Utiliser IndexFlatIP (produit scalaire) avec vecteurs normalisés = cosinus
        self._index = self._faiss.IndexFlatIP(self._dimension)
        self._metadata = []
        self._chunk_data = []
        self._id_to_idx = {}
        logger.info("Nouvel index FAISS initialisé (dim=%d)", self._dimension)

    def _save(self):
        """Sauvegarde l'index FAISS et les métadonnées sur le disque."""
        try:
            self._faiss.write_index(self._index, str(self._get_index_path()))
            with open(self._get_metadata_path(), "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, ensure_ascii=False, indent=2)
            with open(self._get_chunk_data_path(), "wb") as f:
                pickle.dump(self._chunk_data, f)
            logger.debug("Index FAISS sauvegardé (%d vecteurs)", self._index.ntotal)
        except Exception as e:
            logger.error("Erreur sauvegarde index FAISS : %s", e)

    def _normalize_embeddings(self, embeddings: List[List[float]]) -> np.ndarray:
        """Normalise les embeddings pour la similarité cosinus avec IndexFlatIP."""
        arr = np.array(embeddings, dtype=np.float32)
        self._faiss.normalize_L2(arr)
        return arr

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Ajoute des chunks à la base vectorielle.

        Génère les embeddings et stocke avec métadonnées.
        Évite les doublons basés sur source_path + chunk_index.

        Returns:
            Nombre de chunks ajoutés (nouveaux)
        """
        if not chunks:
            return 0

        # Vérifier les doublons existants
        existing_ids = set(self._id_to_idx.keys())

        # Filtrer les nouveaux chunks
        new_chunks = []
        for chunk in chunks:
            chunk_id = f"{chunk.source_path}_{chunk.chunk_index}"
            if chunk_id not in existing_ids:
                new_chunks.append((chunk_id, chunk))

        if not new_chunks:
            logger.info("Aucun nouveau chunk à ajouter (tous existent déjà)")
            return 0

        logger.info("Génération des embeddings pour %d nouveaux chunks...", len(new_chunks))
        chunk_objects = [c for _, c in new_chunks]
        embeddings = embed_chunks(chunk_objects)

        # Normaliser pour similarité cosinus
        normalized_embeddings = self._normalize_embeddings(embeddings)

        # Ajouter à l'index
        self._index.add(normalized_embeddings)

        # Mettre à jour métadonnées et mapping
        start_idx = len(self._metadata)
        for i, (chunk_id, chunk) in enumerate(new_chunks):
            self._id_to_idx[chunk_id] = start_idx + i
            self._metadata.append({
                "id": chunk_id,
                "source": str(chunk.source_path),
                "source_name": chunk.source_path.name,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number if chunk.page_number is not None else -1,
                "document_type": chunk.document_type,
            })
            self._chunk_data.append(chunk)

        # Sauvegarder
        self._save()

        logger.info("%d chunk(s) ajouté(s) à la base vectorielle (total: %d)",
                    len(new_chunks), self._index.ntotal)
        return len(new_chunks)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = None,
        score_threshold: float = None,
    ) -> List[Dict[str, Any]]:
        """Recherche les chunks les plus similaires.

        Args:
            query_embedding: Embedding de la requête
            top_k: Nombre de résultats (défaut: config)
            score_threshold: Seuil de similarité minimum (défaut: config)

        Returns:
            Liste de dicts avec keys: id, document, metadata, distance, similarity
        """
        if top_k is None:
            top_k = rag_settings.RAG_TOP_K
        if score_threshold is None:
            score_threshold = rag_settings.RAG_SCORE_THRESHOLD

        if self._index.ntotal == 0:
            logger.warning("Base vectorielle vide")
            return []

        # Normaliser la requête
        query_arr = self._normalize_embeddings([query_embedding])

        # Recherche
        actual_top_k = min(top_k, self._index.ntotal)
        distances, indices = self._index.search(query_arr, actual_top_k)

        # FAISS IndexFlatIP renvoie le produit scalaire (plus grand = plus similaire)
        # Pour vecteurs normalisés, produit scalaire = cosinus (entre -1 et 1)
        chunks = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx == -1:
                continue

            similarity = float(distances[0][i])  # déjà normalisé = cosinus

            if similarity >= score_threshold:
                meta = self._metadata[idx]
                chunk = self._chunk_data[idx]
                chunks.append({
                    "id": meta["id"],
                    "document": chunk.content,
                    "metadata": meta,
                    "distance": 1.0 - similarity,  # distance = 1 - cosinus
                    "similarity": similarity,
                })

        logger.info("Recherche vectorielle FAISS : %d résultat(s) au-dessus du seuil %.2f",
                    len(chunks), score_threshold)
        return chunks

    def get_stats(self) -> Dict[str, Any]:
        """Renvoie des statistiques sur la base vectorielle."""
        count = self._index.ntotal if self._index else 0

        doc_types = {}
        sources = set()
        for meta in self._metadata:
            dt = meta.get("document_type", "unknown")
            doc_types[dt] = doc_types.get(dt, 0) + 1
            sources.add(meta.get("source_name", "unknown"))

        return {
            "total_chunks": count,
            "document_types": doc_types,
            "unique_sources": len(sources),
            "source_names": sorted(sources),
            "persist_path": str(self.persist_path),
            "embedding_dimension": self._dimension,
        }

    def reset(self) -> bool:
        """Supprime tout l'index (utile pour re-indexer)."""
        try:
            self._init_empty_index()
            self._save()
            # Supprimer les fichiers
            for f in [self._get_index_path(), self._get_metadata_path(), self._get_chunk_data_path()]:
                if f.exists():
                    f.unlink()
            logger.info("Index FAISS réinitialisé")
            return True
        except Exception as e:
            logger.error("Erreur réinitialisation index : %s", e)
            return False

    def delete_by_source(self, source_path: str) -> int:
        """Supprime tous les chunks d'une source donnée.

        Note: FAISS ne supporte pas la suppression efficace.
        Cette méthode marque les entrées comme supprimées mais ne libère pas l'espace.
        Pour une vraie suppression, utilisez reset() + ré-ingestion.
        """
        logger.warning("Suppression par source non supportée efficacement avec FAISS. Utilisez reset().")
        return 0


# Instance globale
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Renvoie l'instance singleton du vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store