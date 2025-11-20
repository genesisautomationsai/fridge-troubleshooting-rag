#!/usr/bin/env python3
"""
Test the hybrid document processor (size-based routing)
"""

import os
import time
from rag_pipeline.document_processor import DocumentProcessor

def test_hybrid_processor():
    """Test size-based routing between Docling and PyMuPDF"""

    print("=" * 60)
    print("TESTING HYBRID DOCUMENT PROCESSOR")
    print("=" * 60)

    # Initialize processor with 20MB threshold
    processor = DocumentProcessor(size_threshold_mb=20.0)

    # Get PDFs from cache (already downloaded from GCS)
    cache_dir = "./data/cache"

    if not os.path.exists(cache_dir):
        print(f"\n❌ Cache directory not found: {cache_dir}")
        print("Please run ingest_manuals.py first to download PDFs")
        return

    # Get all PDFs in cache
    pdf_files = [f for f in os.listdir(cache_dir) if f.endswith('.pdf')]

    if not pdf_files:
        print(f"\n❌ No PDF files found in {cache_dir}")
        return

    print(f"\nFound {len(pdf_files)} PDF files in cache")
    print()

    # Process each PDF
    results = []

    for i, pdf_file in enumerate(pdf_files, 1):
        file_path = os.path.join(cache_dir, pdf_file)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        print(f"\n[{i}/{len(pdf_files)}] {pdf_file}")
        print(f"  Size: {file_size_mb:.2f} MB")

        # Time the processing
        start_time = time.time()

        try:
            result = processor.process_local_document(file_path)

            elapsed = time.time() - start_time

            results.append({
                "file": pdf_file,
                "size_mb": file_size_mb,
                "processor": result["metadata"]["processor"],
                "pages": result["pages"],
                "chars": len(result["text"]),
                "time": elapsed
            })

            print(f"  ✓ Success in {elapsed:.2f}s")
            print(f"    Pages: {result['pages']}")
            print(f"    Characters: {len(result['text']):,}")
            print(f"    Time per page: {elapsed/result['pages']:.3f}s")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                "file": pdf_file,
                "size_mb": file_size_mb,
                "error": str(e)
            })

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    docling_results = [r for r in results if r.get("processor") == "docling"]
    pymupdf_results = [r for r in results if r.get("processor") == "pymupdf"]

    if docling_results:
        avg_time_docling = sum(r["time"] for r in docling_results) / len(docling_results)
        avg_pages_docling = sum(r["pages"] for r in docling_results) / len(docling_results)
        print(f"\nDocling ({len(docling_results)} files <20MB):")
        print(f"  Average time: {avg_time_docling:.2f}s per file")
        print(f"  Average pages: {avg_pages_docling:.0f}")
        print(f"  Speed: {avg_time_docling/avg_pages_docling:.3f}s per page")

    if pymupdf_results:
        avg_time_pymupdf = sum(r["time"] for r in pymupdf_results) / len(pymupdf_results)
        avg_pages_pymupdf = sum(r["pages"] for r in pymupdf_results) / len(pymupdf_results)
        print(f"\nPyMuPDF ({len(pymupdf_results)} files ≥20MB):")
        print(f"  Average time: {avg_time_pymupdf:.2f}s per file")
        print(f"  Average pages: {avg_pages_pymupdf:.0f}")
        print(f"  Speed: {avg_time_pymupdf/avg_pages_pymupdf:.3f}s per page")

    if docling_results and pymupdf_results:
        speedup = (avg_time_docling/avg_pages_docling) / (avg_time_pymupdf/avg_pages_pymupdf)
        print(f"\n📊 PyMuPDF is {speedup:.1f}x faster than Docling")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_hybrid_processor()
