#!/usr/bin/env python3
"""
Setup Qdrant Collection

Initialize Qdrant collection for fridge manuals.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_pipeline.vector_store import QdrantStore
from dotenv import load_dotenv

load_dotenv()


def setup_qdrant(force_recreate: bool = False):
    """
    Set up Qdrant collection.

    Args:
        force_recreate: If True, delete and recreate collection
    """
    print("="*60)
    print("QDRANT SETUP")
    print("="*60)

    # Initialize store
    store = QdrantStore()

    print(f"\nQdrant URL: {store.url}")
    print(f"Collection name: {store.collection_name}")
    print(f"Embedding dimension: {store.embedding_dim}")

    # Create collection
    store.create_collection(force_recreate=force_recreate)

    # Get collection info
    try:
        info = store.get_collection_info()

        print("\n" + "="*60)
        print("COLLECTION INFO")
        print("="*60)
        print(f"Name: {info['name']}")
        print(f"Vectors: {info['vectors_count']}")
        print(f"Points: {info['points_count']}")
        print(f"Status: {info['status']}")
        print(f"Dimension: {info['config']['dimension']}")
        print(f"Distance: {info['config']['distance']}")
        print("="*60)

        print("\n✓ Qdrant setup complete!")
        print(f"\nDashboard: {store.url}/dashboard")

    except Exception as e:
        print(f"\n✗ Error getting collection info: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup Qdrant collection")
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Delete and recreate collection if it exists"
    )

    args = parser.parse_args()

    setup_qdrant(force_recreate=args.force_recreate)
