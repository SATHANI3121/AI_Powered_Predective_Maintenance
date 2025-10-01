"""
Build document index for RAG using Azure AI Search if configured; otherwise fallback to FAISS local index.
"""

from __future__ import annotations

import os
import glob
import pickle
from typing import List

from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_manual_texts(pattern: str) -> List[str]:
    docs: List[str] = []
    for fp in glob.glob(pattern):
        try:
            for page in PyPDFLoader(fp).load():
                docs.append(page.page_content)
        except Exception:
            continue
    return docs


def build_faiss_index(texts: List[str], out_dir: str = "rag") -> None:
    import numpy as np
    import faiss

    model_name = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    model = SentenceTransformer(model_name)
    embs = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(np.array(embs, dtype="float32"))
    os.makedirs(out_dir, exist_ok=True)
    faiss.write_index(index, os.path.join(out_dir, "faiss.index"))
    with open(os.path.join(out_dir, "chunks.pkl"), "wb") as f:
        pickle.dump(texts, f)


def main():
    data_glob = os.getenv("RAG_PDF_GLOB", "seed_data/manuals/*.pdf")
    use_azure = os.getenv("VECTOR_BACKEND", "faiss").lower() == "azure-search"

    raw_docs = load_manual_texts(data_glob)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_text("\n\n".join(raw_docs))

    if use_azure and os.getenv("AZURE_SEARCH_ENDPOINT") and os.getenv("AZURE_SEARCH_KEY"):
        # Azure AI Search ingestion
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.indexes import SearchIndexClient
        from azure.search.documents.indexes.models import (
            SearchIndex,
            SimpleField,
            SearchableField,
            VectorSearch,
            HnswAlgorithmConfiguration,
            VectorSearchAlgorithmKind,
            VectorSearchProfile,
            VectorSearchAlgorithmConfiguration,
            SearchFieldDataType,
            SearchField,
        )
        from azure.search.documents import SearchClient

        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        key = os.getenv("AZURE_SEARCH_KEY")
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "pdm-manuals")

        credential = AzureKeyCredential(key)
        index_client = SearchIndexClient(endpoint, credential)

        # Create index if not exists (simple text + vector field)
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchField(
                name="contentVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                vector_search_dimensions=384,
                vector_search_profile_name="v2"
            ),
        ]

        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="hnsw")
            ],
            profiles=[
                VectorSearchProfile(name="v2", algorithm_configuration_name="hnsw")
            ],
        )

        index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
        try:
            index_client.create_index(index)
        except Exception:
            pass  # index may already exist

        # Embed and upload
        model_name = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        model = SentenceTransformer(model_name)
        embs = model.encode(chunks, show_progress_bar=True, normalize_embeddings=True)

        search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
        batch = []
        for i, (text, vec) in enumerate(zip(chunks, embs)):
            batch.append({
                "id": str(i),
                "content": text,
                "contentVector": vec.tolist(),
            })
            if len(batch) == 1000:
                search_client.upload_documents(batch)
                batch = []
        if batch:
            search_client.upload_documents(batch)
    else:
        build_faiss_index(chunks)


if __name__ == "__main__":
    main()


