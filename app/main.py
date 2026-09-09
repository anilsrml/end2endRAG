import hashlib
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Chunk, Document
from app.schemas import DocumentResponse, HealthResponse, QueryRequest, QueryResponse
from app.services.chunking import chunk_sections
from app.services.clients import EmbeddingClient, ExternalServiceError
from app.services.graph import RAGService
from app.services.parsing import DocumentParseError, parse_document

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    description="PostgreSQL hybrid search kullanan kaynaklı RAG API'si.",
    version="0.1.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/chat")


@app.get("/chat", include_in_schema=False)
def chat_page() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health/live", response_model=HealthResponse, tags=["health"])
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health/ready", response_model=HealthResponse, tags=["health"])
def ready(session: Session = Depends(get_db)) -> HealthResponse:
    try:
        extension = session.scalar(
            text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="PostgreSQL bağlantısı hazır değil.") from exc
    if not extension:
        raise HTTPException(status_code=503, detail="pgvector extension hazır değil.")
    return HealthResponse(status="ready")


@app.post(
    "/api/v1/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
def upload_document(
    file: UploadFile = File(...), session: Session = Depends(get_db)
) -> DocumentResponse:
    filename = Path(file.filename or "").name
    data = file.file.read(settings.max_upload_bytes + 1)
    if not filename:
        raise HTTPException(status_code=422, detail="Dosya adı eksik.")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413, detail=f"Dosya {settings.max_upload_mb} MB sınırını aşıyor."
        )

    digest = hashlib.sha256(data).hexdigest()
    existing = session.scalar(select(Document).where(Document.sha256 == digest))
    if existing:
        count = session.scalar(
            select(func.count()).select_from(Chunk).where(Chunk.document_id == existing.id)
        )
        return _document_response(existing, count or 0)

    try:
        media_type, sections = parse_document(filename, data)
        chunks = chunk_sections(sections)
        vectors = EmbeddingClient(settings).embed([chunk.content for chunk in chunks])
    except DocumentParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ExternalServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    document_id = uuid.uuid4()
    storage_path = settings.uploads_dir / f"{document_id}{Path(filename).suffix.lower()}"
    try:
        storage_path.write_bytes(data)
        document = Document(
            id=document_id,
            filename=filename,
            media_type=media_type,
            sha256=digest,
            storage_path=str(storage_path),
            status="ready",
            document_metadata={"section_count": len(sections)},
        )
        session.add(document)
        session.add_all(
            [
                Chunk(
                    document_id=document_id,
                    position=chunk.position,
                    content=chunk.content,
                    page=chunk.page,
                    heading=chunk.heading,
                    token_count=chunk.token_count,
                    embedding=embedding,
                )
                for chunk, embedding in zip(chunks, vectors, strict=True)
            ]
        )
        session.commit()
        session.refresh(document)
    except Exception:
        session.rollback()
        storage_path.unlink(missing_ok=True)
        raise
    return _document_response(document, len(chunks))


@app.get("/api/v1/documents", response_model=list[DocumentResponse], tags=["documents"])
def list_documents(session: Session = Depends(get_db)) -> list[DocumentResponse]:
    rows = session.execute(
        select(Document, func.count(Chunk.id))
        .outerjoin(Chunk)
        .group_by(Document.id)
        .order_by(Document.created_at.desc())
    )
    return [_document_response(document, count) for document, count in rows]


@app.get("/api/v1/documents/{document_id}", response_model=DocumentResponse, tags=["documents"])
def get_document(document_id: uuid.UUID, session: Session = Depends(get_db)) -> DocumentResponse:
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")
    count = session.scalar(
        select(func.count()).select_from(Chunk).where(Chunk.document_id == document.id)
    )
    return _document_response(document, count or 0)


@app.delete("/api/v1/documents/{document_id}", status_code=204, tags=["documents"])
def delete_document(document_id: uuid.UUID, session: Session = Depends(get_db)) -> None:
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")
    storage_path = Path(document.storage_path)
    session.delete(document)
    session.commit()
    storage_path.unlink(missing_ok=True)


@app.post("/api/v1/query", response_model=QueryResponse, tags=["rag"])
def query(request: QueryRequest, session: Session = Depends(get_db)) -> QueryResponse:
    try:
        result, trace_id = RAGService(settings).answer(
            session, request.question.strip(), request.document_ids
        )
    except ExternalServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return QueryResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        model=settings.openrouter_model,
        reranker_used=result.get("reranker_used", False),
        trace_id=trace_id,
    )


def _document_response(document: Document, chunk_count: int) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        media_type=document.media_type,
        status=document.status,
        chunk_count=chunk_count,
        created_at=document.created_at,
    )

