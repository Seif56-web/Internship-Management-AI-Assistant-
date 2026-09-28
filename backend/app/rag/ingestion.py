"""CLI d'ingestion des documents pour le RAG.

Usage:
    python -m app.rag.ingestion              # Ingestion par défaut (config)
    python -m app.rag.ingestion --reset      # Reset + ingestion
    python -m app.rag.ingestion --stats      # Stats seulement
    python -m app.rag.ingestion --test "query"  # Test de recherche
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Ajouter le backend au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.rag.service import get_rag_service
from app.rag.config import rag_settings


async def run_ingestion(reset: bool = False, paths: list = None) -> bool:
    """Exécute l'ingestion complète."""
    service = get_rag_service()

    if reset:
        logger.info("Remise à zéro de la base vectorielle...")
        service.reset_database()

    await service.initialize()

    result = service.ingest_documents(paths)

    if result["success"]:
        logger.info("✅ Ingestion réussie !")
        logger.info("   Chunks bruts: %d", result["raw_chunks"])
        logger.info("   Chunks finaux: %d", result["final_chunks"])
        logger.info("   Nouveaux ajoutés: %d", result["chunks_added"])
        logger.info("   Total en base: %d", result["total_in_db"])
        logger.info("   Sources: %s", ", ".join(result["sources"]))
        return True
    else:
        logger.error("❌ Échec ingestion : %s", result.get("error", "inconnu"))
        return False


async def show_stats():
    """Affiche les statistiques de la base vectorielle."""
    service = get_rag_service()
    await service.initialize()

    stats = service.get_stats()
    logger.info("=== STATISTIQUES BASE VECTORIELLE ===")
    logger.info("Total chunks: %d", stats["total_chunks"])
    logger.info("Types de documents: %s", stats["document_types"])
    logger.info("Sources uniques: %d", stats["unique_sources"])
    logger.info("Noms des sources: %s", ", ".join(stats["source_names"]))
    logger.info("Chemin de persistance: %s", stats["persist_path"])
    logger.info("Dimension embeddings: %d", stats["embedding_dimension"])


async def test_retrieval(query: str):
    """Teste la recherche RAG pour une requête."""
    service = get_rag_service()
    await service.initialize()

    logger.info("=== TEST RECHERCHE RAG ===")
    logger.info("Requête: %s", query)

    result = service.query(query)

    if not result["enabled"]:
        logger.warning("RAG désactivé")
        return

    logger.info("Chunks trouvés: %d", result["chunks_found"])

    if result["chunks"]:
        for i, chunk in enumerate(result["chunks"], 1):
            logger.info("  [%d] %s (sim=%.3f)", i, chunk.citation, chunk.similarity)
            logger.info("       %s...", chunk.content[:150].replace("\n", " "))

    logger.info("\n--- CONTEXTE FORMATÉ ---")
    print(result["context"])

    logger.info("\n--- SOURCES ---")
    print(result["sources"])


def main():
    parser = argparse.ArgumentParser(description="Pipeline RAG - Ingestion et test")
    parser.add_argument("--reset", action="store_true", help="Reset la base avant ingestion")
    parser.add_argument("--stats", action="store_true", help="Affiche les stats seulement")
    parser.add_argument("--test", type=str, help="Teste une requête de recherche")
    parser.add_argument("--paths", nargs="*", help="Chemins spécifiques à indexer")

    args = parser.parse_args()

    if args.stats:
        asyncio.run(show_stats())
    elif args.test:
        asyncio.run(test_retrieval(args.test))
    else:
        success = asyncio.run(run_ingestion(reset=args.reset, paths=args.paths))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()