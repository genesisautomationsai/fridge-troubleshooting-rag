"""
Embedding Generation using OpenAI

Create vector embeddings for text chunks using OpenAI's embedding models.
"""

import os
from typing import List, Dict
from openai import OpenAI
from llama_index.core.schema import TextNode
from dotenv import load_dotenv
import time

load_dotenv()


class OpenAIEmbedder:
    """Generate embeddings using OpenAI API"""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        batch_size: int = 100
    ):
        """
        Initialize OpenAI embedder.

        Args:
            api_key: OpenAI API key
            model: Embedding model (default: text-embedding-3-small)
            batch_size: Number of texts to embed per API call
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.batch_size = batch_size

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)

        # Embedding dimension (text-embedding-3-small = 1536)
        self.embedding_dim = 1536 if "small" in self.model else 3072

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats (embedding vector)
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1

            print(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)...")

            try:
                # Create embeddings for batch
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )

                # Extract embeddings
                embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(embeddings)

                # Rate limiting - small pause between batches
                if i + self.batch_size < len(texts):
                    time.sleep(0.5)

            except Exception as e:
                print(f"✗ Error embedding batch {batch_num}: {e}")
                # Add None placeholders for failed batch
                all_embeddings.extend([None] * len(batch))

        print(f"✓ Embedded {len(all_embeddings)} texts")
        return all_embeddings

    def embed_nodes(self, nodes: List[TextNode]) -> List[Dict]:
        """
        Embed TextNode objects and return with metadata.

        Args:
            nodes: List of TextNode objects

        Returns:
            List of dictionaries with text, embedding, and metadata
        """
        # Extract texts from nodes
        texts = [node.text for node in nodes]

        # Generate embeddings
        embeddings = self.embed_texts(texts)

        # Combine with metadata
        embedded_docs = []
        for node, embedding in zip(nodes, embeddings):
            if embedding is not None:
                embedded_docs.append({
                    "id": node.node_id,
                    "text": node.text,
                    "embedding": embedding,
                    "metadata": node.metadata
                })

        return embedded_docs

    def get_embedding_stats(self, embeddings: List[List[float]]) -> Dict:
        """
        Get statistics about embeddings.

        Args:
            embeddings: List of embedding vectors

        Returns:
            Dictionary with embedding statistics
        """
        valid_embeddings = [e for e in embeddings if e is not None]

        return {
            "total": len(embeddings),
            "valid": len(valid_embeddings),
            "failed": len(embeddings) - len(valid_embeddings),
            "dimension": len(valid_embeddings[0]) if valid_embeddings else 0,
            "model": self.model
        }


def embed_chunks(
    chunks: List[TextNode],
    model: str = "text-embedding-3-small",
    batch_size: int = 100
) -> List[Dict]:
    """
    Convenience function to embed chunks.

    Args:
        chunks: List of TextNode objects
        model: OpenAI embedding model
        batch_size: Batch size for API calls

    Returns:
        List of dictionaries with embeddings
    """
    embedder = OpenAIEmbedder(model=model, batch_size=batch_size)
    return embedder.embed_nodes(chunks)


# Example usage
if __name__ == "__main__":
    # Example 1: Embed single text
    embedder = OpenAIEmbedder()

    text = "Samsung refrigerator ice maker troubleshooting guide"
    embedding = embedder.embed_text(text)

    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

    # Example 2: Embed multiple texts
    texts = [
        "Ice maker not producing ice",
        "Refrigerator temperature too warm",
        "Water dispenser not working"
    ]

    embeddings = embedder.embed_texts(texts)
    print(f"\nEmbedded {len(embeddings)} texts")

    # Example 3: Embed TextNodes
    from llama_index.core.schema import TextNode

    nodes = [
        TextNode(text=text, metadata={"source": "manual.pdf"})
        for text in texts
    ]

    embedded_docs = embedder.embed_nodes(nodes)
    print(f"\nCreated {len(embedded_docs)} embedded documents")
    print(f"First doc keys: {embedded_docs[0].keys()}")
