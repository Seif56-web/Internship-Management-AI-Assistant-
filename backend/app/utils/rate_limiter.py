"""Limiteur de débit simple en mémoire (fenêtre glissante par utilisateur)."""
import time
from collections import defaultdict, deque
from threading import Lock

from app.config import settings

_buckets: dict = defaultdict(deque)
_lock = Lock()


def check_rate_limit(user_id: int) -> bool:
    """Renvoie True si l'utilisateur peut envoyer un message, False s'il est limité."""
    window = settings.CHAT_RATE_LIMIT_WINDOW_SECONDS
    limit = settings.CHAT_RATE_LIMIT_MAX
    now = time.monotonic()

    with _lock:
        bucket = _buckets[user_id]
        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= limit:
            return False

        bucket.append(now)
        return True


def reset_rate_limits() -> None:
    """Vide tous les compteurs (utilisé par les tests)."""
    with _lock:
        _buckets.clear()
