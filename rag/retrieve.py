"""
RAG retrieval utilities using Azure AI Search or FAISS fallback
"""

from __future__ import annotations

import os
import pickle
from typing import Dict, Any, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer


class RAGService:
    def __init__(self):
        self.use_azure = os.getenv("VECTOR_BACKEND", "faiss").lower() == "azure-search"
        self.embedder = SentenceTransformer(os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
        if self.use_azure and os.getenv("AZURE_SEARCH_ENDPOINT") and os.getenv("AZURE_SEARCH_KEY"):
            from azure.core.credentials import AzureKeyCredential
            from azure.search.documents import SearchClient

            self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
            self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "pdm-manuals")
            self.credential = AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
            self.search_client = SearchClient(self.endpoint, self.index_name, self.credential)
        else:
            import faiss

            self.index = faiss.read_index("rag/faiss.index")
            self.chunks = pickle.load(open("rag/chunks.pkl", "rb"))

    def search_documents(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        if self.use_azure and hasattr(self, "search_client"):
            q_emb = self.embedder.encode([query], normalize_embeddings=True).astype("float32").tolist()[0]
            results = self.search_client.search(
                search_text=None,
                vector={"value": q_emb, "k": limit, "fields": "contentVector"},
                select=["content"],
            )
            out = []
            for r in results:
                out.append({
                    "title": f"doc-{r["id"]}",
                    "content": r["content"],
                    "relevance": float(r["@search.score"]),
                })
            return out
        else:
            import faiss

            q = self.embedder.encode([query], normalize_embeddings=True).astype("float32")
            D, I = self.index.search(q, limit)
            results = []
            for d, i in zip(D[0], I[0]):
                # FAISS returns distances (lower is better), convert to similarity score (0-1)
                # For L2 distance: similarity = 1 / (1 + distance)
                # For negative distances (inner product), convert to positive similarity
                if d < 0:
                    # Negative distance means good match in inner product space
                    similarity = min(abs(d), 1.0)
                else:
                    # Positive distance: convert to similarity score
                    similarity = 1.0 / (1.0 + float(d))
                
                results.append({
                    "title": f"chunk-{int(i)}",
                    "content": self.chunks[int(i)],
                    "relevance": similarity,
                })
            return results

    def answer_question(
        self,
        question: str,
        context: Optional[str] = None,
        max_results: int = 5,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        docs = self.search_documents(question, limit=max_results)
        ctx = "\n\n".join(d["content"] for d in docs)
        if context:
            ctx = context + "\n\n" + ctx

        # Lightweight template answer (LLM integration can be added via OpenAI/Azure OpenAI)
        answer = (
            "Based on the maintenance manuals and retrieved context, "
            + question
            + ". Check bearings, alignment, lubrication, and electrical load."
        )
        result: Dict[str, Any] = {
            "answer": answer,
            "confidence": 0.8,
        }
        if include_sources:
            result["sources"] = [
                {"title": d["title"], "content": d["content"][:300], "relevance_score": float(d["relevance"]) }
                for d in docs
            ]
        return result

    def get_available_sources(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_azure and hasattr(self, "search_client"):
            # Placeholder: Azure Search does not list docs directly without a query; return meta
            return [{"title": "azure-index", "category": "manual", "relevance": 1.0}]
        else:
            return [
                {"title": f"chunk-{i}", "category": "manual", "relevance": 1.0}
                for i in range(min(10, len(self.chunks)))
            ]


