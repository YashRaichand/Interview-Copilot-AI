import numpy as np
import hashlib
import logging
import asyncio

logger = logging.getLogger(__name__)


class SemanticMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._lock = asyncio.Lock()

    async def load_model(self):
        if self._model is not None:
            return
        async with self._lock:
            if self._model is not None:
                return
            try:
                from sentence_transformers import SentenceTransformer
                loop = asyncio.get_event_loop()
                self._model = await loop.run_in_executor(None, lambda: SentenceTransformer(self.model_name))
                logger.info(f"Sentence transformer '{self.model_name}' loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load sentence transformer: {e}")
                raise

    async def encode(self, text: str) -> np.ndarray:
        cache_key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
        from app.utils.redis_client import redis_client
        cached = await redis_client.get_json(cache_key)
        if cached:
            return np.array(cached, dtype=np.float32)

        await self.load_model()
        text = text[:10000]

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, lambda: self._model.encode(text, normalize_embeddings=True, show_progress_bar=False))
        embedding = np.array(embedding, dtype=np.float32)

        await redis_client.set_json(cache_key, embedding.tolist(), ex=86400)
        return embedding

    async def encode_batch(self, texts: list) -> np.ndarray:
        await self.load_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, lambda: self._model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False))
        return np.array(embeddings, dtype=np.float32)

    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm1 * norm2))

    async def similarity(self, text1: str, text2: str) -> float:
        emb1, emb2 = await asyncio.gather(self.encode(text1), self.encode(text2))
        return self.cosine_similarity(emb1, emb2)


semantic_matcher = SemanticMatcher()
