# end2endRAG

FastAPI, LangGraph ve PostgreSQL/pgvector ile geliştirilmiş kaynaklı hybrid RAG projesi. Bu proje, AI/LLM Backend Engineer rolleri için retrieval, model entegrasyonu, gözlemlenebilirlik ve tekrar üretilebilir kurulum yetkinliklerini göstermek amacıyla hazırlanıyor.

## Özellikler

- Markdown ve metin tabanlı PDF yükleme
- OpenAI `text-embedding-3-small` embeddings
- pgvector cosine search + PostgreSQL Türkçe full-text search
- Reciprocal Rank Fusion ile hybrid retrieval
- Opsiyonel Cohere reranking
- OpenRouter üzerinden değiştirilebilir LLM
- LangGraph sorgu akışı ve LangSmith tracing
- Swagger ve küçük chat arayüzü
- Docker Compose ile tek komutluk kurulum

## Mimari

```text
Swagger / Chat UI -> FastAPI -> LangGraph
                                 |-- pgvector search
                                 |-- PostgreSQL full-text search
                                 |-- RRF -> optional Cohere rerank
                                 `-- OpenRouter LLM -> cited answer
```

## Gereksinimler

- Windows üzerinde Docker Desktop
- OpenAI API anahtarı
- OpenRouter API anahtarı ve model slug'ı
- İsteğe bağlı Cohere ve LangSmith anahtarları


## Hızlı başlangıç

```bash
cp .env.example .env
```

`.env` içinde en az şu alanları doldur:

```dotenv
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=provider/model-slug
```

Ardından Windows PowerShell veya Docker erişimi olan terminalde:

```bash
docker compose up --build
```

- Chat: http://localhost:8000/chat
- Swagger: http://localhost:8000/docs
- Readiness: http://localhost:8000/health/ready

Swagger'daki `POST /api/v1/documents` endpointinden bir `.md` veya `.pdf` yükle, ardından `POST /api/v1/query` ile soru sor.

## Geliştirme

`uv` kuruluysa:

```bash
uv sync --dev
uv run pytest
uv run ruff check .
```

Migration:

```bash
uv run alembic upgrade head
```

## Gizlilik

- `.env`, API anahtarları ve yüklenen belgeler Git'e eklenmez.
- LangSmith tracing açılırsa soru, getirilen pasajlar ve yanıt LangSmith'e gönderilebilir.
- OpenRouter istekleri ZDR sağlayıcı koşuluyla gönderilir.
- Kişisel belgeleri public repoya ekleme.

## İlk sürüm sınırları

- OCR yoktur.
- Konuşma hafızası yoktur.
- Çok kullanıcılı auth yoktur.
- Elasticsearch yoktur.
- Cloud deployment hedeflenmemektedir.

