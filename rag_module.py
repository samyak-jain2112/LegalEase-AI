"""
RAG (Retrieval-Augmented Generation) module for LegalEase.
Handles text chunking, embedding, vector storage, and similarity-based retrieval.
Uses ChromaDB for the in-memory vector store and sentence-transformers for embeddings.
"""

import streamlit as st
import chromadb
from sentence_transformers import SentenceTransformer
import hashlib


@st.cache_resource(show_spinner=False)
def _load_embedding_model():
    """Load and cache the sentence-transformer embedding model."""
    return SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text_for_rag(text, chunk_size=500, overlap=50):
    """
    Split text into overlapping chunks for better semantic coverage.

    Args:
        text: The full cleaned document text.
        chunk_size: Maximum number of characters per chunk.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    if not text or not text.strip():
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size

        if end >= text_len:
            chunks.append(text[start:].strip())
            break

        # Try to break at a sentence boundary (period followed by space)
        break_point = text.rfind('. ', start, end)
        if break_point == -1 or break_point <= start:
            # Fall back to a word boundary (space)
            break_point = text.rfind(' ', start, end)
        if break_point == -1 or break_point <= start:
            # No good break point; cut at chunk_size
            break_point = end
        else:
            break_point += 1  # include the space/period

        chunk = text[start:break_point].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward with overlap
        start = max(start + 1, break_point - overlap)

    return chunks


def build_vector_store(text):
    """
    Chunk the document text, compute embeddings, and store in ChromaDB.

    Args:
        text: The full cleaned document text.

    Returns:
        A tuple of (chromadb.Collection, list[str] chunks).
    """
    model = _load_embedding_model()
    chunks = chunk_text_for_rag(text)

    if not chunks:
        return None, []

    # Create a unique collection name based on text content hash
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
    collection_name = f"legalease_{text_hash}"

    # Create an ephemeral (in-memory) ChromaDB client
    client = chromadb.Client()

    # Delete collection if it already exists (re-upload scenario)
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # Compute embeddings for all chunks at once
    embeddings = model.encode(chunks, show_progress_bar=False).tolist()

    # Add to ChromaDB
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
    )

    return collection, chunks


def retrieve_relevant_chunks(collection, query, top_k=5):
    """
    Retrieve the most relevant chunks for a given query using similarity search.

    Args:
        collection: The ChromaDB collection.
        query: The user query or search string.
        top_k: Number of top results to return.

    Returns:
        A single string with the top-k chunks joined by double newlines.
    """
    if collection is None:
        return ""

    model = _load_embedding_model()
    query_embedding = model.encode([query], show_progress_bar=False).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, collection.count()),
    )

    if results and results["documents"] and results["documents"][0]:
        return "\n\n".join(results["documents"][0])

    return ""


def get_all_chunks(chunks):
    """
    Return all chunks as a list. Used by Map-Reduce summarization and translation.

    Args:
        chunks: The list of text chunks from build_vector_store.

    Returns:
        The same list of chunks (pass-through for clarity in calling code).
    """
    return chunks if chunks else []
