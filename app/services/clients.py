from collections.abc import Sequence

import httpx
from openai import OpenAI

from app.config import Settings


class ExternalServiceError(RuntimeError):
    pass


class EmbeddingClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not self.settings.openai_api_key:
            raise ExternalServiceError("OPENAI_API_KEY yapılandırılmamış.")

        client = OpenAI(api_key=self.settings.openai_api_key)
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 64):
            response = client.embeddings.create(
                model=self.settings.openai_embedding_model,
                input=list(texts[start : start + 64]),
                encoding_format="float",
                dimensions=self.settings.openai_embedding_dimensions,
            )
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend(item.embedding for item in ordered)
        return vectors


class OpenRouterClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def answer(self, question: str, context: str) -> str:
        if not self.settings.openrouter_api_key or not self.settings.openrouter_model:
            raise ExternalServiceError(
                "OPENROUTER_API_KEY ve OPENROUTER_MODEL yapılandırılmalıdır."
            )

        payload = {
            "model": self.settings.openrouter_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Yalnızca verilen kaynakları kullanarak Türkçe cevap ver. "
                        "Her iddiayı [1], [2] biçiminde kaynak numarasıyla ilişkilendir. "
                        "Kaynaklarda yeterli bilgi yoksa bunu açıkça söyle ve tahmin yürütme."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Kaynaklar:\n{context}\n\nSoru: {question}",
                },
            ],
            "temperature": 0.1,
            "max_tokens": 800,
            "provider": {"zdr": True, "allow_fallbacks": True},
        }
        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    f"{self.settings.openrouter_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "X-OpenRouter-Title": self.settings.app_name,
                    },
                    json=payload,
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise ExternalServiceError("OpenRouter yanıt üretimi başarısız oldu.") from exc


class CohereReranker:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.cohere_api_key)

    def rerank(self, query: str, documents: Sequence[str], top_n: int) -> list[tuple[int, float]]:
        if not self.enabled:
            return []
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    "https://api.cohere.com/v2/rerank",
                    headers={
                        "Authorization": f"Bearer {self.settings.cohere_api_key}",
                        "Content-Type": "application/json",
                        "X-Client-Name": self.settings.app_name,
                    },
                    json={
                        "model": self.settings.cohere_rerank_model,
                        "query": query,
                        "documents": list(documents),
                        "top_n": top_n,
                    },
                )
                response.raise_for_status()
                return [
                    (item["index"], float(item["relevance_score"]))
                    for item in response.json()["results"]
                ]
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return []
