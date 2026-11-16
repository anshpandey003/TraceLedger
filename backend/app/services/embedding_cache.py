from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


MODEL_CACHE_SCHEMA_VERSION = 1
DEFAULT_DIMENSIONS = 768


class EmbeddingCache:
    """Persistent, model-aware cache for query and document embeddings."""

    def __init__(
        self,
        db_path: str | Path | None = None,
    ) -> None:
        if db_path is None:
            backend_root = Path(__file__).resolve().parents[2]
            db_path = (
                backend_root
                / ".cache"
                / "embedding_cache.sqlite3"
            )

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._stats_lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "corruptions": 0,
        }

        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            str(self.db_path),
            timeout=30,
        )

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute("PRAGMA busy_timeout=30000")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    cache_key TEXT PRIMARY KEY,
                    namespace TEXT NOT NULL,
                    model TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @staticmethod
    def _fingerprint(
        *,
        namespace: str,
        model: str,
        dimensions: int,
        content: str,
    ) -> str:
        payload = {
            "schema_version": MODEL_CACHE_SCHEMA_VERSION,
            "namespace": namespace,
            "model": model,
            "dimensions": dimensions,
            "content": content,
        }

        canonical_payload = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical_payload.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _validate_embedding(
        embedding: object,
        dimensions: int,
    ) -> list[float]:
        if not isinstance(embedding, list):
            raise ValueError("Embedding must be a list.")

        if len(embedding) != dimensions:
            raise ValueError(
                f"Expected {dimensions} dimensions, "
                f"received {len(embedding)}."
            )

        validated: list[float] = []

        for value in embedding:
            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ):
                raise ValueError("Embedding contains a non-numeric value.")

            numeric_value = float(value)

            if not math.isfinite(numeric_value):
                raise ValueError("Embedding contains a non-finite value.")

            validated.append(numeric_value)

        return validated

    def get(
        self,
        *,
        namespace: str,
        model: str,
        dimensions: int,
        content: str,
    ) -> list[float] | None:
        if not namespace or not model or not content:
            raise ValueError(
                "Namespace, model, and content must be non-empty."
            )

        if dimensions <= 0:
            raise ValueError("Dimensions must be greater than zero.")

        cache_key = self._fingerprint(
            namespace=namespace,
            model=model,
            dimensions=dimensions,
            content=content,
        )

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT embedding_json
                FROM embedding_cache
                WHERE cache_key = ?
                """,
                (cache_key,),
            ).fetchone()

            if row is None:
                self._increment("misses")
                return None

            try:
                decoded = json.loads(row[0])
                embedding = self._validate_embedding(
                    decoded,
                    dimensions,
                )
            except (ValueError, TypeError, json.JSONDecodeError):
                connection.execute(
                    """
                    DELETE FROM embedding_cache
                    WHERE cache_key = ?
                    """,
                    (cache_key,),
                )
                self._increment("corruptions")
                self._increment("misses")
                return None

        self._increment("hits")
        return embedding

    def set(
        self,
        *,
        namespace: str,
        model: str,
        dimensions: int,
        content: str,
        embedding: list[float],
    ) -> None:
        if not namespace or not model or not content:
            raise ValueError(
                "Namespace, model, and content must be non-empty."
            )

        if dimensions <= 0:
            raise ValueError("Dimensions must be greater than zero.")

        validated = self._validate_embedding(
            embedding,
            dimensions,
        )

        cache_key = self._fingerprint(
            namespace=namespace,
            model=model,
            dimensions=dimensions,
            content=content,
        )

        embedding_json = json.dumps(
            validated,
            separators=(",", ":"),
            allow_nan=False,
        )

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO embedding_cache (
                    cache_key,
                    namespace,
                    model,
                    dimensions,
                    embedding_json
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    embedding_json = excluded.embedding_json,
                    created_at = CURRENT_TIMESTAMP
                """,
                (
                    cache_key,
                    namespace,
                    model,
                    dimensions,
                    embedding_json,
                ),
            )

        self._increment("writes")

    def _increment(self, key: str) -> None:
        with self._stats_lock:
            self._stats[key] += 1

    @property
    def stats(self) -> dict[str, int]:
        with self._stats_lock:
            return self._stats.copy()

    def reset_stats(self) -> None:
        with self._stats_lock:
            for key in self._stats:
                self._stats[key] = 0
