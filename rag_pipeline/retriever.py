"""
RAG Retriever

Query the RAG system to retrieve relevant manual content.
"""

from typing import List, Dict, Optional
from .embedding import OpenAIEmbedder
from .vector_store import QdrantStore


class RAGRetriever:
    """Retrieve relevant documents using RAG pipeline"""

    def __init__(
        self,
        embedder: Optional[OpenAIEmbedder] = None,
        vector_store: Optional[QdrantStore] = None
    ):
        """
        Initialize RAG retriever.

        Args:
            embedder: OpenAI embedder instance
            vector_store: Qdrant store instance
        """
        self.embedder = embedder or OpenAIEmbedder()
        self.vector_store = vector_store or QdrantStore()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        min_score: float = 0.0
    ) -> Dict:
        """
        Retrieve relevant documents for a query.

        Args:
            query: User query
            top_k: Number of results to return
            filters: Optional metadata filters
            min_score: Minimum similarity score threshold

        Returns:
            Dictionary with retrieved documents and metadata
        """
        # 1. Embed query
        query_embedding = self.embedder.embed_text(query)

        # 2. Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )

        # 3. Filter by minimum score
        filtered_results = [
            r for r in results
            if r["score"] >= min_score
        ]

        # 4. Format response
        return {
            "query": query,
            "top_k": top_k,
            "total_results": len(filtered_results),
            "results": filtered_results,
            "context": self._build_context(filtered_results)
        }

    def _build_context(self, results: List[Dict]) -> str:
        """
        Build context string from retrieved documents.

        Args:
            results: List of search results

        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant information found."

        context_parts = []

        for i, result in enumerate(results, 1):
            source = result["metadata"].get("source", "Unknown")
            text = result["text"]
            score = result["score"]

            context_parts.append(
                f"[{i}] (Source: {source}, Relevance: {score:.2f})\n{text}\n"
            )

        return "\n".join(context_parts)

    def retrieve_with_metadata(
        self,
        query: str,
        top_k: int = 5,
        brand: Optional[str] = None,
        product_type: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict:
        """
        Retrieve with metadata filtering.

        Args:
            query: User query
            top_k: Number of results
            brand: Filter by brand (e.g., "Samsung")
            product_type: Filter by product type (e.g., "refrigerator", "microwave")
            model: Filter by model number

        Returns:
            Dictionary with retrieved documents
        """
        # Build filters - map product_type to appliance_type (actual metadata field)
        filters = {}
        if brand:
            filters["brand"] = brand
        if product_type:
            filters["appliance_type"] = product_type  # Fixed: use appliance_type
        if model:
            filters["model_number"] = model  # Fixed: use model_number

        return self.retrieve(
            query=query,
            top_k=top_k,
            filters=filters if filters else None
        )


def search_manuals_rag(
    query: str,
    top_k: int = 5,
    brand: Optional[str] = "Samsung",
    product_type: Optional[str] = "refrigerator"
) -> dict:
    """
    Convenience function for searching manuals (compatible with agent tools).

    Args:
        query: Search query
        top_k: Number of results
        brand: Brand filter
        product_type: Product type filter

    Returns:
        Dictionary with search results in agent-compatible format
    """
    retriever = RAGRetriever()

    result = retriever.retrieve_with_metadata(
        query=query,
        top_k=top_k,
        brand=brand,
        product_type=product_type
    )

    # Format for agent compatibility
    return {
        "status": "success",
        "query": query,
        "found_information": result["total_results"] > 0,
        "context": result["context"],
        "results": result["results"],
        "source": "RAG System (Qdrant + OpenAI)",
        "num_results": result["total_results"]
    }


# Example usage
if __name__ == "__main__":
    # Initialize retriever
    retriever = RAGRetriever()

    # Example query
    query = "My ice maker is not producing ice"

    # Retrieve relevant documents
    result = retriever.retrieve(query, top_k=3)

    print(f"Query: {result['query']}")
    print(f"Results found: {result['total_results']}")
    print(f"\nContext:\n{result['context']}")

    # Retrieve with filters
    result_filtered = retriever.retrieve_with_metadata(
        query=query,
        top_k=3,
        brand="Samsung",
        product_type="refrigerator"
    )

    print(f"\n\nFiltered results: {result_filtered['total_results']}")
