import re


def _normalize(message: str) -> str:
    return re.sub(r"[^a-zà-ÿ0-9\s]", "", message.lower()).strip()


async def generate_response(message: str) -> str:
    """Réponse de démonstration déterministe pour la phase 1.

    Aucun accès aux données ni appel LLM à ce stade :
    le flux complet frontend -> backend -> frontend est validé,
    et le LLM sera branché dans une phase ultérieure.
    """
    normalized = _normalize(message)

    if not normalized:
        return "Je n'ai pas compris votre demande. Pouvez-vous reformuler ?"

    greetings = ("bonjour", "salut", "hello", "bonsoir", "coucou", "hi")
    thanks = ("merci", "super", "parfait", "génial", "cool")
    farewell = ("au revoir", "bye", "bientôt", "bientot", "adieu")

    if any(word in normalized for word in greetings):
        return "Bonjour ! Je suis l'assistant de gestion des stagiaires. Comment puis-je vous aider ?"

    if any(word in normalized for word in thanks):
        return "Avec plaisir ! N'hésitez pas si vous avez d'autres questions."

    if any(word in normalized for word in farewell):
        return "Au revoir ! À bientôt sur la plateforme de gestion des stagiaires."

    if any(word in normalized for word in ("aide", "help", "quoi", "qui es")):
        return (
            "Je suis l'assistant de la plateforme de gestion des stagiaires Hutchinson. "
            "Dans cette première version, je peux répondre à des messages simples. "
            "Les questions sur les stagiaires, encadrants, évaluations, rapports et attestations "
            "seront disponibles dans les prochaines versions."
        )

    return (
        "J'ai bien reçu votre message. Pour l'instant, mes réponses sont limitées "
        "aux salutations et aux questions générales. Les fonctionnalités avancées "
        "(accès aux données, historique des conversations) arriveront dans les prochaines phases."
    )