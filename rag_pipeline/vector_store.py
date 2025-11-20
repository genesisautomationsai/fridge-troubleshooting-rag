"""
Qdrant Vector Store

Store and retrieve vector embeddings using Qdrant.
"""

import os
import uuid
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from dotenv import load_dotenv

load_dotenv()


class QdrantStore:
    """Qdrant vector store for embeddings"""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_dim: int = 1536
    ):
        """
        Initialize Qdrant client.

        Args:
            url: Qdrant server URL
            api_key: Qdrant API key (for cloud)
            collection_name: Collection name for vectors
            embedding_dim: Dimension of embeddings (1536 for OpenAI small)
        """
        self.url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = api_key or os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "fridge_manuals")
        self.embedding_dim = embedding_dim

        # Initialize Qdrant client
        if self.api_key:
            self.client = QdrantClient(url=self.url, api_key=self.api_key)
        else:
            self.client = QdrantClient(url=self.url)

    def create_collection(self, force_recreate: bool = False):
        """
        Create Qdrant collection.

        Args:
            force_recreate: If True, delete existing collection first
        """
        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_exists = any(c.name == self.collection_name for c in collections)

        if collection_exists and force_recreate:
            print(f"Deleting existing collection: {self.collection_name}")
            self.client.delete_collection(self.collection_name)
            collection_exists = False

        if not collection_exists:
            print(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            print(f"✓ Collection created: {self.collection_name}")
        else:
            print(f"Collection already exists: {self.collection_name}")

    def add_documents(
        self,
        documents: List[Dict],
        batch_size: int = 100
    ) -> int:
        """
        Add documents with embeddings to Qdrant.

        Args:
            documents: List of dicts with 'text', 'embedding', 'metadata'
            batch_size: Number of documents per batch

        Returns:
            Number of documents added
        """
        points = []

        for doc in documents:
            # Generate unique ID if not provided
            doc_id = doc.get("id", str(uuid.uuid4()))

            # Create point
            point = PointStruct(
                id=doc_id,
                vector=doc["embedding"],
                payload={
                    "text": doc["text"],
                    **doc.get("metadata", {})
                }
            )
            points.append(point)

        # Upload in batches
        total_batches = (len(points) + batch_size - 1) // batch_size

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            batch_num = i // batch_size + 1

            print(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} documents)...")

            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )

        print(f"✓ Added {len(points)} documents to {self.collection_name}")
        return len(points)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of matching documents with scores
        """
        # Build filter if provided
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                query_filter = Filter(must=conditions)

        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=query_filter
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.id,
                "score": result.score,
                "text": result.payload.get("text", ""),
                "metadata": {
                    k: v for k, v in result.payload.items()
                    if k != "text"
                }
            })

        return formatted_results

    def delete_collection(self):
        """Delete the collection"""
        self.client.delete_collection(self.collection_name)
        print(f"✓ Deleted collection: {self.collection_name}")

    def get_collection_info(self) -> Dict:
        """
        Get information about the collection.

        Returns:
            Dictionary with collection stats
        """
        info = self.client.get_collection(self.collection_name)

        return {
            "name": self.collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status,
            "config": {
                "dimension": self.embedding_dim,
                "distance": "cosine"
            }
        }


# Example usage
if __name__ == "__main__":
    # Initialize store
    store = QdrantStore()

    # Create collection
    store.create_collection(force_recreate=True)

    # Example documents with embeddings
    documents = [
        {
            "id": "doc1",
            "text": "Ice maker not producing ice",
            "embedding": [0.1] * 1536,  # Dummy embedding
            "metadata": {
                "source": "manual1.pdf",
                "page": 42,
                "category": "ice_maker"
            }
        },
        {
            "id": "doc2",
            "text": "Refrigerator temperature too warm",
            "embedding": [0.2] * 1536,  # Dummy embedding
            "metadata": {
                "source": "manual1.pdf",
                "page": 15,
                "category": "temperature"
            }
        }
    ]

    # Add documents
    store.add_documents(documents)

    # Get collection info
    info = store.get_collection_info()
    print(f"\nCollection info:")
    print(f"  Vectors: {info['vectors_count']}")
    print(f"  Points: {info['points_count']}")

    # Search
    query_embedding = [0.15] * 1536  # Dummy query
    results = store.search(query_embedding, top_k=2)

    print(f"\nSearch results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['text']} (score: {result['score']:.4f})")
