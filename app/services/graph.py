import uuid
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.config import Settings
from app.services.clients import CohereReranker, EmbeddingClient, OpenRouterClient
from app.services.retrieval import HybridRetriever, RetrievedChunk


class RAGState(TypedDict, total=False):
    question: str
    document_ids: list[uuid.UUID]
    candidates: list[RetrievedChunk]
    selected: list[RetrievedChunk]
    reranker_used: bool
    answer: str
    sources: list[dict[str, Any]]


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embeddings = EmbeddingClient(settings)
        self.retriever = HybridRetriever(settings)
        self.reranker = CohereReranker(settings)
        self.llm = OpenRouterClient(settings)

    def answer(
        self,
        session: Session,
        question: str,
        document_ids: list[uuid.UUID],
    ) -> tuple[RAGState, str]:
        trace_id = uuid.uuid4()

        def retrieve(state: RAGState) -> RAGState:
            embedding = self.embeddings.embed([state["question"]])[0]
            candidates = self.retriever.search(
                session, state["question"], embedding, state.get("document_ids", [])
            )
            return {"candidates": candidates}

        def rerank(state: RAGState) -> RAGState:
            candidates = state.get("candidates", [])
            if not candidates or not self.reranker.enabled:
                return {
                    "selected": candidates[: self.settings.final_chunks],
                    "reranker_used": False,
                }
            scores = self.reranker.rerank(
                state["question"],
                [candidate.content for candidate in candidates],
                self.settings.final_chunks,
            )
            if not scores:
                return {
                    "selected": candidates[: self.settings.final_chunks],
                    "reranker_used": False,
                }
            selected: list[RetrievedChunk] = []
            for index, score in scores:
                candidate = candidates[index]
                candidate.score = score
                selected.append(candidate)
            return {"selected": selected, "reranker_used": True}

        def generate(state: RAGState) -> RAGState:
            selected = state.get("selected", [])
            if not selected:
                return {
                    "answer": (
                        "Yüklenen belgelerde bu soruyu cevaplamak için yeterli bilgi bulamadım."
                    ),
                    "sources": [],
                }
            context = "\n\n".join(
                f"[{index}] {item.filename}"
                f"{f' — sayfa {item.page}' if item.page else ''}"
                f"{f' — {item.heading}' if item.heading else ''}\n{item.content}"
                for index, item in enumerate(selected, start=1)
            )
            answer = self.llm.answer(state["question"], context)
            sources = [
                {
                    "document_id": item.document_id,
                    "filename": item.filename,
                    "page": item.page,
                    "heading": item.heading,
                    "excerpt": item.content[:500],
                    "score": item.score,
                }
                for item in selected
            ]
            return {"answer": answer, "sources": sources}

        builder = StateGraph(RAGState)
        builder.add_node("retrieve", retrieve)
        builder.add_node("rerank", rerank)
        builder.add_node("generate", generate)
        builder.add_edge(START, "retrieve")
        builder.add_edge("retrieve", "rerank")
        builder.add_edge("rerank", "generate")
        builder.add_edge("generate", END)
        graph = builder.compile()
        result = graph.invoke(
            {"question": question, "document_ids": document_ids},
            config={"run_id": trace_id, "run_name": "hybrid-rag-query"},
        )
        return result, str(trace_id)
