import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Chunk, Document
from app.services.ranking import reciprocal_rank_fusion


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    content: str
    page: int | None
    heading: str | None
    score: float


class HybridRetriever:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def search(
        self,
        session: Session,
        question: str,
        query_embedding: list[float],
        document_ids: list[uuid.UUID],
    ) -> list[RetrievedChunk]:
        vector = self._vector_search(session, query_embedding, document_ids)
        keyword = self._keyword_search(session, question, document_ids)
        fused = reciprocal_rank_fusion(
            [
                [(str(item.chunk_id), item) for item in vector],
                [(str(item.chunk_id), item) for item in keyword],
            ],
            limit=self.settings.rerank_candidates,
        )
        for item in fused:
            item.value.score = item.score
        return [item.value for item in fused]

    def _vector_search(
        self, session: Session, embedding: list[float], document_ids: list[uuid.UUID]
    ) -> list[RetrievedChunk]:
        distance = Chunk.embedding.cosine_distance(embedding)
        statement = (
            select(Chunk, Document.filename, (1 - distance).label("score"))
            .join(Document, Document.id == Chunk.document_id)
            .where(Document.status == "ready")
            .order_by(distance)
            .limit(self.settings.vector_candidates)
        )
        if document_ids:
            statement = statement.where(Chunk.document_id.in_(document_ids))
        return [self._from_row(row) for row in session.execute(statement)]

    def _keyword_search(
        self, session: Session, question: str, document_ids: list[uuid.UUID]
    ) -> list[RetrievedChunk]:
        query = func.websearch_to_tsquery(text("'turkish'::regconfig"), question)
        rank = func.ts_rank_cd(Chunk.search_vector, query)
        statement = (
            select(Chunk, Document.filename, rank.label("score"))
            .join(Document, Document.id == Chunk.document_id)
            .where(Document.status == "ready", Chunk.search_vector.op("@@")(query))
            .order_by(rank.desc())
            .limit(self.settings.keyword_candidates)
        )
        if document_ids:
            statement = statement.where(Chunk.document_id.in_(document_ids))
        return [self._from_row(row) for row in session.execute(statement)]

    @staticmethod
    def _from_row(row) -> RetrievedChunk:
        chunk, filename, score = row
        return RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            filename=filename,
            content=chunk.content,
            page=chunk.page,
            heading=chunk.heading,
            score=float(score),
        )
