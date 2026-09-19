import os
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer

class DocumentRetriever:
    def __init__(self):
        # Resolve path relative to backend root or absolute
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_persist = os.path.join(base_dir, "knowledge_base", "processed")
        self.persist_dir = os.getenv("CHROMA_PERSIST_DIR", default_persist)
        os.makedirs(self.persist_dir, exist_ok=True)
        
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        from chromadb.config import Settings
        
        # Initialize persistent client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="environmental_docs",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Load local embedding model
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """Embed and upsert documents into ChromaDB."""
        if not documents:
            return
        embeddings = self.encoder.encode(documents).tolist()
        self.collection.upsert(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, n_results: int = 4, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query vector database and return structured items with text, metadata, and relevance score.
        """
        if self.collection.count() == 0:
            return []
            
        query_embedding = self.encoder.encode([query]).tolist()
        
        where_filter = {"category": category_filter} if category_filter else None
        
        try:
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min(n_results, self.collection.count()),
                where=where_filter
            )
        except Exception:
            # Fallback without where filter if category doesn't match
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min(n_results, self.collection.count())
            )
            
        formatted_results = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [""] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.2] * len(docs)
            
            for doc, meta, doc_id, dist in zip(docs, metas, ids, distances):
                # Cosine distance to similarity percentage
                similarity = max(0.0, min(1.0, 1.0 - float(dist)))
                formatted_results.append({
                    "id": doc_id,
                    "text": doc,
                    "metadata": meta,
                    "relevance_score": round(similarity, 3)
                })
                
        return formatted_results

    def count(self) -> int:
        return self.collection.count()

retriever = DocumentRetriever()
