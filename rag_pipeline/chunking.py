"""
Document Chunking using LlamaIndex

Split documents into semantic chunks for embedding and retrieval.
"""

from typing import List, Dict, Optional
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode


class LlamaIndexChunker:
    """Chunk documents using LlamaIndex SentenceSplitter"""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separator: str = " "
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of overlapping tokens between chunks
            separator: Separator for splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize LlamaIndex sentence splitter
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=separator
        )

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[TextNode]:
        """
        Chunk a single text document.

        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of TextNode objects
        """
        # Create Document
        doc = Document(
            text=text,
            metadata=metadata or {}
        )

        # Split into nodes
        nodes = self.splitter.get_nodes_from_documents([doc])

        return nodes

    def chunk_documents(
        self,
        documents: List[Dict[str, any]]
    ) -> List[TextNode]:
        """
        Chunk multiple documents.

        Args:
            documents: List of document dictionaries with 'text' and 'metadata'

        Returns:
            List of TextNode objects
        """
        all_nodes = []

        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})

            # Add source info to metadata
            if "gcs_uri" in doc:
                metadata["source"] = doc["gcs_uri"]
            elif "file_path" in doc:
                metadata["source"] = doc["file_path"]

            # Chunk document
            nodes = self.chunk_text(text, metadata)
            all_nodes.extend(nodes)

        print(f"✓ Created {len(all_nodes)} chunks from {len(documents)} documents")

        return all_nodes

    def get_chunk_stats(self, nodes: List[TextNode]) -> Dict:
        """
        Get statistics about chunks.

        Args:
            nodes: List of TextNode objects

        Returns:
            Dictionary with chunk statistics
        """
        chunk_lengths = [len(node.text) for node in nodes]

        return {
            "total_chunks": len(nodes),
            "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0,
            "min_chunk_length": min(chunk_lengths) if chunk_lengths else 0,
            "max_chunk_length": max(chunk_lengths) if chunk_lengths else 0,
            "total_characters": sum(chunk_lengths)
        }


def chunk_documents(
    text_or_documents: any,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    metadata: Optional[Dict] = None
) -> List[TextNode]:
    """
    Convenience function to chunk documents.

    Args:
        text_or_documents: Either a string or list of document dicts
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks
        metadata: Optional metadata (used if text_or_documents is string)

    Returns:
        List of TextNode objects
    """
    chunker = LlamaIndexChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    # Handle single string
    if isinstance(text_or_documents, str):
        return chunker.chunk_text(text_or_documents, metadata)

    # Handle list of documents
    elif isinstance(text_or_documents, list):
        return chunker.chunk_documents(text_or_documents)

    else:
        raise ValueError("Input must be string or list of document dicts")


# Example usage
if __name__ == "__main__":
    # Example 1: Chunk a single text
    text = "This is a sample manual text. " * 100
    nodes = chunk_documents(
        text,
        chunk_size=256,
        chunk_overlap=25,
        metadata={"source": "test_manual.pdf"}
    )

    print(f"Created {len(nodes)} chunks")
    print(f"First chunk: {nodes[0].text[:100]}...")

    # Example 2: Chunk multiple documents
    documents = [
        {
            "text": "Manual 1 content...",
            "metadata": {"source": "manual1.pdf"}
        },
        {
            "text": "Manual 2 content...",
            "metadata": {"source": "manual2.pdf"}
        }
    ]

    all_nodes = chunk_documents(documents)
    print(f"Total chunks from all docs: {len(all_nodes)}")
