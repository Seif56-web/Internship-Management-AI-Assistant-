"""Abstraction du fournisseur LLM (assistant conversationnel).

Le fournisseur est isolé derrière une interface unique : le reste du code
appelle uniquement `get_llm_provider()` puis `complete(...)`.

- OpenAICompatibleProvider : API REST compatible OpenAI (/chat/completions).
- DummyProvider : utilisé quand aucune clé API n'est configurée ; il ne fait
  aucun appel réseau et laisse le chat_service répondre de façon déterministe.

La clé API ne doit être fournie que via la configuration (variable d'environnement).
"""
import json
import logging
from typing import List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Tu es l'assistant conversationnel de la plateforme de gestion des stagiaires Hutchinson. "
    "Tu réponds en français, de façon claire et concise. "
    "Tu ne dois JAMAIS inventer des données métier (stagiaires, encadrants, évaluations, "
    "rapports, attestations, validations) : tu réponds uniquement à partir des informations fournies "
    "dans le contexte. Si l'information n'est pas dans le contexte, dis-le honnêtement. "
    "Le contexte peut contenir deux types d'informations :\n"
    "1. CONTEXTE BASE DE DONNÉES (TEMPS RÉEL) : données actuelles de la plateforme (listes de stagiaires, "
    "notes, statuts, attestations, validations). C'est la SOURCE DE VÉRITÉ pour les faits métier.\n"
    "2. CONTEXTE DOCUMENTAIRE (RAG) : extraits de documents indexés (procédures, conventions, rapports, "
    "grilles d'évaluation). C'est une CONNAISSANCE DOCUMENTAIRE, pas des données temps réel.\n"
    "Utilise le contexte base de données pour les faits chiffrés et statuts actuels. "
    "Utilise le contexte documentaire pour les explications de procédures, critères, règles. "
    "Ne confonds jamais les deux : les documents décrivent des règles générales, la base donne les faits actuels. "
    "Les questions sur les rapports, évaluations, validations ou attestations concernent les stagiaires "
    "de la plateforme : quand le contexte fournit une liste de stagiaires, utilise-la pour répondre "
    "même si le terme exact (rapport, évaluation, validation...) diffère. "
    "N'utilise aucune balise Markdown (pas de **, *, #, -, backticks) : réponds en texte brut "
    "avec des retours à la ligne simples. "
    "Les notes et moyennes des évaluations sont calculées par le système (moyenne des critères "
    "sur 5, convertie sur 20) et fournies dans le contexte : utilise-les telles quelles, ne les "
    "recalcule pas et n'en invente jamais. "
    "Pour les réponses générales (hors données), tu peux répondre librement."
)


class LLMProviderError(Exception):
    """Erreur d'appel au fournisseur LLM."""


class LLMProvider:
    """Interface du fournisseur LLM."""

    async def complete(self, messages: List[dict], max_tokens: Optional[int] = None) -> str:
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    """Fournisseur OpenAI-compatible (OpenAI, Azure, Ollama, LM Studio, ...)."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int,
        temperature: float,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.temperature = temperature

    async def complete(self, messages: List[dict], max_tokens: Optional[int] = None) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    content=json.dumps(payload),
                )
        except httpx.HTTPError as e:
            logger.error("Erreur réseau LLM (%s) : %s", self.base_url, e)
            raise LLMProviderError(f"Erreur de connexion au fournisseur LLM : {e}") from e

        if response.status_code != 200:
            logger.error("Erreur LLM %s : %s", response.status_code, response.text[:500])
            raise LLMProviderError(
                f"Le fournisseur LLM a renvoyé une erreur {response.status_code}"
            )

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError, TypeError) as e:
            logger.error("Réponse LLM inattendue : %s", response.text[:500])
            raise LLMProviderError("Réponse LLM invalide") from e

        return content.strip()


class DummyProvider(LLMProvider):
    """Fournisseur de repli quand le LLM n'est pas configuré (aucun appel réseau)."""

    async def complete(self, messages: List[dict], max_tokens: Optional[int] = None) -> str:
        return ""


def get_llm_provider() -> LLMProvider:
    base_url = settings.LLM_BASE_URL.rstrip("/")

    # Ollama local : aucune clé API n'est nécessaire
    if "localhost:11434" in base_url or "127.0.0.1:11434" in base_url:
        logger.info(
            "Utilisation du LLM local Ollama | modèle=%s | URL=%s",
            settings.LLM_MODEL,
            settings.LLM_BASE_URL,
        )
        return OpenAICompatibleProvider(
            api_key="",
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            temperature=settings.LLM_TEMPERATURE,
        )

    # Fournisseur distant : nécessite une clé API
    if settings.LLM_API_KEY:
        return OpenAICompatibleProvider(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            temperature=settings.LLM_TEMPERATURE,
        )

    logger.warning("Aucun fournisseur LLM configuré : utilisation du DummyProvider")
    return DummyProvider()
