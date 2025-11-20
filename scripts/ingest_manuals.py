#!/usr/bin/env python3
"""
Manual Ingestion Script

Process PDF manuals from GCS and ingest into RAG system:
1. Extract text using Docling (local, open-source)
2. Chunk using LlamaIndex
3. Embed using OpenAI
4. Store in Qdrant
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_pipeline.document_processor import DocumentProcessor
from rag_pipeline.chunking import LlamaIndexChunker
from rag_pipeline.embedding import OpenAIEmbedder
from rag_pipeline.vector_store import QdrantStore
from dotenv import load_dotenv

load_dotenv()


def ingest_manuals_from_gcs(
    gcs_uris: list[str],
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    batch_size: int = 100
):
    """
    Ingest manuals from GCS into RAG system.

    Args:
        gcs_uris: List of GCS URIs (gs://bucket/path/file.pdf)
        chunk_size: Chunk size for splitting
        chunk_overlap: Overlap between chunks
        batch_size: Batch size for embedding/uploading
    """
    print("="*60)
    print("MANUAL INGESTION PIPELINE")
    print("="*60)
    print(f"Manuals to process: {len(gcs_uris)}")
    print(f"Chunk size: {chunk_size}")
    print(f"Chunk overlap: {chunk_overlap}")
    print(f"Batch size: {batch_size}")
    print("="*60)

    # Step 1: Initialize components
    print("\n[1/5] Initializing components...")
    doc_processor = DocumentProcessor()
    chunker = LlamaIndexChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    embedder = OpenAIEmbedder(batch_size=batch_size)
    vector_store = QdrantStore()

    # Step 2: Extract text from PDFs
    print("\n[2/5] Extracting text from PDFs using Docling...")
    documents = []

    for i, gcs_uri in enumerate(gcs_uris, 1):
        print(f"\nProcessing {i}/{len(gcs_uris)}: {gcs_uri}")

        try:
            # Extract text
            result = doc_processor.process_gcs_document(gcs_uri)

            # Extract metadata from URI
            filename = gcs_uri.split("/")[-1].replace(".pdf", "")
            parts = filename.split("_")

            metadata = {
                "source": gcs_uri,
                "filename": filename,
                "pages": result["pages"],
                "brand": parts[0] if len(parts) > 0 else "Unknown",
                "product_type": parts[2].lower() if len(parts) > 2 else "appliance",
                "model": parts[1] if len(parts) > 1 else "Unknown"
            }

            documents.append({
                "text": result["text"],
                "metadata": metadata,
                "gcs_uri": gcs_uri
            })

            print(f"  ✓ Extracted {len(result['text'])} characters, {result['pages']} pages")

        except Exception as e:
            print(f"  ✗ Failed: {e}")

    print(f"\n✓ Successfully processed {len(documents)}/{len(gcs_uris)} documents")

    # Step 3: Chunk documents
    print("\n[3/5] Chunking documents with LlamaIndex...")
    all_chunks = chunker.chunk_documents(documents)

    stats = chunker.get_chunk_stats(all_chunks)
    print(f"✓ Created {stats['total_chunks']} chunks")
    print(f"  Avg length: {stats['avg_chunk_length']:.0f} characters")
    print(f"  Min/Max: {stats['min_chunk_length']}/{stats['max_chunk_length']}")

    # Step 4: Generate embeddings
    print("\n[4/5] Generating embeddings with OpenAI...")
    embedded_docs = embedder.embed_nodes(all_chunks)

    embed_stats = embedder.get_embedding_stats([d["embedding"] for d in embedded_docs])
    print(f"✓ Generated {embed_stats['valid']} embeddings")
    print(f"  Model: {embed_stats['model']}")
    print(f"  Dimension: {embed_stats['dimension']}")

    # Step 5: Store in Qdrant
    print("\n[5/5] Storing vectors in Qdrant...")
    num_stored = vector_store.add_documents(embedded_docs, batch_size=batch_size)

    print(f"✓ Stored {num_stored} vectors in Qdrant")

    # Final summary
    print("\n" + "="*60)
    print("INGESTION COMPLETE")
    print("="*60)
    print(f"Documents processed: {len(documents)}")
    print(f"Chunks created: {len(all_chunks)}")
    print(f"Vectors stored: {num_stored}")
    print("="*60)

    # Collection info
    info = vector_store.get_collection_info()
    print(f"\nCollection: {info['name']}")
    print(f"Total vectors: {info['vectors_count']}")
    print(f"Total points: {info['points_count']}")


def main():
    parser = argparse.ArgumentParser(description="Ingest manuals into RAG system")

    parser.add_argument(
        "--gcs-uris",
        nargs="+",
        help="GCS URIs of PDF manuals"
    )

    parser.add_argument(
        "--gcs-prefix",
        help="GCS prefix to process all PDFs (e.g., gs://bucket/manuals/)"
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Chunk size in tokens (default: 512)"
    )

    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Chunk overlap in tokens (default: 50)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for embedding/uploading (default: 100)"
    )

    args = parser.parse_args()

    # Get GCS URIs
    gcs_uris = []

    if args.gcs_uris:
        gcs_uris = args.gcs_uris
    elif args.gcs_prefix:
        # List all PDFs in prefix
        from google.cloud import storage

        bucket_name = args.gcs_prefix.replace("gs://", "").split("/")[0]
        prefix = "/".join(args.gcs_prefix.replace("gs://", "").split("/")[1:])

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)

        for blob in blobs:
            if blob.name.endswith(".pdf"):
                gcs_uris.append(f"gs://{bucket_name}/{blob.name}")

        print(f"Found {len(gcs_uris)} PDFs in {args.gcs_prefix}")
    else:
        print("Error: Must provide either --gcs-uris or --gcs-prefix")
        return

    # Ingest manuals
    ingest_manuals_from_gcs(
        gcs_uris=gcs_uris,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()
