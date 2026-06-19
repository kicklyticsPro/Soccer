"""Cache simple en mémoire pour éviter de réinterroger le même match."""
import hashlib
import time
from typing import Dict, Optional, Any
import threading


class AnalysisCache:
    """Cache TTL en mémoire pour les analyses.

    Pour utiliser un cache persistant (Redis, SQLite), il suffira de remplacer
    ce module. L'API est volontairement simple.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    @staticmethod
    def _make_key(team1: str, team2: str, date: str, competition: str) -> str:
        """Crée une clé hash normalisée."""
        # Normaliser: lowercase, sans accents simples
        s = f"{team1.strip().lower()}|{team2.strip().lower()}|{date.strip().lower()}|{competition.strip().lower()}"
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def get(self, team1: str, team2: str, date: str, competition: str) -> Optional[Dict[str, Any]]:
        """Récupère une analyse cachée si elle existe et n'a pas expiré."""
        key = self._make_key(team1, team2, date, competition)
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            if time.time() - entry["timestamp"] > self._ttl:
                # Expiré
                del self._cache[key]
                return None
            return entry

    def set(self, team1: str, team2: str, date: str, competition: str, data: Dict[str, Any]):
        """Stocke une analyse dans le cache."""
        key = self._make_key(team1, team2, date, competition)
        with self._lock:
            self._cache[key] = {**data, "timestamp": time.time()}

    def clear(self):
        """Vide le cache."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> Dict[str, int]:
        """Retourne des stats sur le cache."""
        with self._lock:
            now = time.time()
            valid = sum(1 for e in self._cache.values() if now - e["timestamp"] <= self._ttl)
            return {"total": len(self._cache), "valid": valid}


# Singleton global
_cache = AnalysisCache(ttl_seconds=3600)  # 1 heure


def get_cache() -> AnalysisCache:
    return _cache
