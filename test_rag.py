#!/usr/bin/env python3
"""Test RAG retrieval"""

from rag_pipeline.retriever import search_manuals_rag

# Test query WITHOUT filters (your PDFs don't have Samsung/refrigerator in filename)
result = search_manuals_rag('ice maker not working', top_k=3, brand=None, product_type=None)

print(f"\n{'='*60}")
print(f"QUERY: 'ice maker not working'")
print(f"{'='*60}")
print(f"Found {len(result['results'])} results\n")

for i, r in enumerate(result['results'], 1):
    print(f"Result {i}:")
    print(f"  Score: {r['score']:.4f}")
    print(f"  Source: {r['metadata'].get('source', 'Unknown')}")
    print(f"  Text: {r['text'][:300]}...")
    print()
