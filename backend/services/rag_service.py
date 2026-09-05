"""
RAG Service — ChromaDB Vector Store for CAD Examples
=====================================================
Embeds build123d snippet pairs (NL description + code) into ChromaDB.
Retrieves top-k most similar examples for few-shot LLM prompting.

Embedding model: sentence-transformers/all-MiniLM-L6-v2  (local, no API key needed)
                 384-dim, fast, great quality for technical text retrieval.
Vector store:    ChromaDB (persistent, local on disk, no server needed)

Advantages of local embeddings over Gemini API:
  - Zero API quota usage (embed as many docs as you want)
  - Works fully offline
  - Consistent quality for CAD/engineering text

Usage:
    # First-time setup (run once, downloads ~90MB model):
    RAGService.build_index()

    # At query time (instant):
    results = RAGService.retrieve("hollow cylinder with 5mm wall", k=3)
    # Returns list of {description, code, similarity}
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from config import BASE_DIR

logger = logging.getLogger("cad_workbench.rag_service")

# ChromaDB persistent storage directory
CHROMA_DIR = BASE_DIR / "rag_corpus" / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

COLLECTION_NAME = "cad_snippets_v1"

# Sentence-transformers model (downloads once, cached in ~/.cache/huggingface/)
_EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
_embed_model = None   # lazy-loaded on first use


def _get_embed_model():
    """Lazy-loads the sentence-transformers model (cached after first call).
    Returns None if the model cannot be loaded (offline / missing package).
    """
    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"[RAG] Loading embedding model '{_EMBED_MODEL_NAME}'...")
            _embed_model = SentenceTransformer(_EMBED_MODEL_NAME)
            logger.info("[RAG] Embedding model ready.")
        except Exception as e:
            logger.warning(
                f"[RAG] Could not load embedding model '{_EMBED_MODEL_NAME}': {e}. "
                "RAG retrieval will be disabled for this session."
            )
            _embed_model = None
    return _embed_model


# ---------------------------------------------------------------------------
# Embedding helpers (local, no API calls)
# ---------------------------------------------------------------------------

def _embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a batch of strings locally via sentence-transformers.
    Returns list of 384-dim float vectors, or empty list if model unavailable.
    """
    model = _get_embed_model()
    if model is None:
        return []
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def _embed_query(query: str) -> List[float]:
    """Embed a single query string for retrieval. Returns [] if model unavailable."""
    results = _embed_texts([query])
    return results[0] if results else []


# ---------------------------------------------------------------------------
# ChromaDB Collection
# ---------------------------------------------------------------------------

def _get_collection():
    """Returns the persistent ChromaDB collection (creates if not exists)."""
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}   # cosine similarity
    )


# ---------------------------------------------------------------------------
# Main RAG Service
# ---------------------------------------------------------------------------

class RAGService:
    """
    Manages the CAD snippet vector store.

    Index:     embed NL descriptions → store in ChromaDB
    Retrieve:  embed user query → find top-k nearest neighbors
    Inject:    format results as few-shot examples for LLM prompt
    """

    @staticmethod
    def build_index(force_rebuild: bool = False) -> int:
        """
        Embeds all examples from the corpus (all weeks) and stores in ChromaDB.
        Skips examples already indexed (by ID) unless force_rebuild=True.
        Returns: number of new documents added.
        """
        from rag_corpus.examples_week4 import EXAMPLES as W4
        from rag_corpus.examples_week5 import EXAMPLES as W5
        from rag_corpus.examples_week8 import EXAMPLES as W8
        from rag_corpus.examples_engineering import EXAMPLES as W_ENG
        from rag_corpus.examples_complex import EXAMPLES as W_CMPLX
        ALL_EXAMPLES = W4 + W5 + W8 + W_ENG + W_CMPLX

        collection = _get_collection()

        if force_rebuild:
            import chromadb
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            try:
                client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass
            collection = client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("[RAG] Force rebuilding index from scratch.")

        # Check which IDs are already indexed
        existing_ids = set(collection.get()["ids"])
        new_examples = [ex for ex in ALL_EXAMPLES if ex["id"] not in existing_ids]

        if not new_examples:
            logger.info(f"[RAG] All {len(ALL_EXAMPLES)} examples already indexed. Skipping.")
            return 0

        logger.info(f"[RAG] Embedding {len(new_examples)} new examples (total corpus: {len(ALL_EXAMPLES)})...")

        texts_to_embed = [
            f"{ex['description']}. Tags: {', '.join(ex['tags'])}"
            for ex in new_examples
        ]

        embeddings = _embed_texts(texts_to_embed)

        collection.add(
            ids=[ex["id"] for ex in new_examples],
            embeddings=embeddings,
            documents=[ex["description"] for ex in new_examples],
            metadatas=[{
                "tags": ", ".join(ex["tags"]),
                "code": ex["code"]
            } for ex in new_examples]
        )

        logger.info(f"[RAG] Successfully indexed {len(new_examples)} new examples. Total: {len(ALL_EXAMPLES)}.")
        return len(new_examples)

    @staticmethod
    def retrieve(query: str, k: int = 3, min_similarity: float = 0.25) -> List[Dict[str, Any]]:
        """
        Retrieves the top-k most similar CAD examples for a given user query.
        Filters out matches below min_similarity threshold to avoid injecting
        irrelevant/misleading few-shot code into the system prompt.

        Returns list of dicts:
            {"description": str, "code": str, "tags": str, "similarity": float}
        """
        collection = _get_collection()

        if collection.count() == 0:
            logger.warning("[RAG] Collection is empty. Run RAGService.build_index() first.")
            return []

        query_embedding = _embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        retrieved = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            similarity = 1.0 - distance   # cosine distance → similarity
            if similarity >= min_similarity:
                meta = results["metadatas"][0][i]
                retrieved.append({
                    "description": results["documents"][0][i],
                    "code": meta.get("code", ""),
                    "tags": meta.get("tags", ""),
                    "similarity": round(similarity, 4)
                })

        if retrieved:
            logger.info(
                f"[RAG] Query: '{query[:50]}...' → "
                f"top match: '{retrieved[0]['description'][:50]}' "
                f"(sim={retrieved[0]['similarity']}) | returned {len(retrieved)}/{k} matches"
            )
        else:
            logger.info(f"[RAG] Query: '{query[:50]}...' → no matches above min_similarity={min_similarity}")

        return retrieved

    @staticmethod
    def format_for_prompt(examples: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved examples as a few-shot block for LLM injection.
        """
        if not examples:
            return ""

        blocks = []
        for i, ex in enumerate(examples, 1):
            tag_str = f" (Tags: {ex['tags']})" if ex.get('tags') else ""
            blocks.append(
                f"## Similar Example {i}: {ex['description']}{tag_str}\n"
                f"```python\n{ex['code'].strip()}\n```"
            )
        return "\n\n".join(blocks)

    @staticmethod
    def index_size() -> int:
        """Returns number of documents currently in the index."""
        return _get_collection().count()
