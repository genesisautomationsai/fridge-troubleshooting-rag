"""
Hybrid Document Processor using Docling + LlamaIndex PyMuPDFReader

- Files <20MB: Docling (high quality, preserves structure)
- Files ≥20MB: LlamaIndex PyMuPDFReader (10-50x faster)

This balances quality and speed for large-scale ingestion.
"""

import os
import hashlib
from typing import Dict, List, Optional
from pathlib import Path
from google.cloud import storage
from docling.document_converter import DocumentConverter
from llama_index.readers.file import PyMuPDFReader
from dotenv import load_dotenv

load_dotenv()


class DocumentProcessor:
    """Hybrid document processor: Docling for small files, PyMuPDFReader for large files"""

    def __init__(self, size_threshold_mb: float = 20.0):
        """
        Initialize hybrid document processor.

        Args:
            size_threshold_mb: File size threshold in MB. Files below use Docling,
                              files above use PyMuPDFReader. Default: 20MB
        """
        # Initialize processors (lazy loaded when needed)
        self.docling_converter = None
        self.pymupdf_reader = None
        self.size_threshold_bytes = size_threshold_mb * 1024 * 1024
        self.size_threshold_mb = size_threshold_mb

        print(f"✓ Hybrid processor initialized")
        print(f"  - Files <{size_threshold_mb}MB: Docling (high quality)")
        print(f"  - Files ≥{size_threshold_mb}MB: LlamaIndex PyMuPDFReader (fast)")

    def _get_docling_converter(self):
        """Lazy load Docling converter"""
        if self.docling_converter is None:
            self.docling_converter = DocumentConverter()
            print("  → Docling converter loaded")
        return self.docling_converter

    def _get_pymupdf_reader(self):
        """Lazy load PyMuPDF reader"""
        if self.pymupdf_reader is None:
            self.pymupdf_reader = PyMuPDFReader()
            print("  → PyMuPDF reader loaded")
        return self.pymupdf_reader

    def _should_use_docling(self, file_path: str) -> bool:
        """
        Determine which processor to use based on file size.

        Args:
            file_path: Path to the file

        Returns:
            True if should use Docling, False if should use PyMuPDF
        """
        file_size = os.path.getsize(file_path)
        use_docling = file_size < self.size_threshold_bytes

        size_mb = file_size / (1024 * 1024)
        processor = "Docling" if use_docling else "PyMuPDF"
        print(f"  → File size: {size_mb:.2f}MB → Using {processor}")

        return use_docling

    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = "md5") -> str:
        """
        Calculate hash of file for duplicate detection.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5' or 'sha256')

        Returns:
            Hex digest of file hash
        """
        if algorithm == "md5":
            hasher = hashlib.md5()
        elif algorithm == "sha256":
            hasher = hashlib.sha256()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    def process_gcs_document(
        self,
        gcs_uri: str,
        cache_dir: str = "./data/cache"
    ) -> Dict[str, any]:
        """
        Process a document from Google Cloud Storage.

        Args:
            gcs_uri: GCS URI (e.g., gs://bucket/path/file.pdf)
            cache_dir: Local directory to cache downloaded PDFs

        Returns:
            Dictionary containing extracted text and metadata
        """
        # Download from GCS to local cache
        os.makedirs(cache_dir, exist_ok=True)

        filename = gcs_uri.split("/")[-1]
        local_path = os.path.join(cache_dir, filename)

        print(f"Downloading from GCS: {gcs_uri}")
        download_from_gcs(gcs_uri, local_path)

        # Process local file
        result = self.process_local_document(local_path)
        result["gcs_uri"] = gcs_uri

        return result

    def process_local_document(
        self,
        file_path: str
    ) -> Dict[str, any]:
        """
        Process a local document file using size-based routing.

        Args:
            file_path: Path to local PDF file

        Returns:
            Dictionary containing extracted text and metadata
        """
        print(f"Processing: {file_path}")

        # Determine which processor to use based on file size
        use_docling = self._should_use_docling(file_path)

        if use_docling:
            # Use Docling for high-quality extraction
            return self._process_with_docling(file_path)
        else:
            # Use PyMuPDF for fast extraction
            return self._process_with_pymupdf(file_path)

    def _process_with_docling(self, file_path: str) -> Dict[str, any]:
        """Process document using Docling (high quality)"""
        converter = self._get_docling_converter()

        # Calculate file hash for duplicate detection
        file_hash = self.get_file_hash(file_path)

        result = converter.convert(file_path)
        text = result.document.export_to_markdown()
        num_pages = len(result.document.pages) if hasattr(result.document, 'pages') else 0

        metadata = {
            "page_count": num_pages,
            "source": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "file_hash": file_hash,  # For duplicate detection
            "processor": "docling"
        }

        print(f"✓ Docling: Extracted {len(text)} characters from {num_pages} pages")
        print(f"  File hash: {file_hash}")

        return {
            "text": text,
            "pages": num_pages,
            "file_path": file_path,
            "metadata": metadata
        }

    def _process_with_pymupdf(self, file_path: str) -> Dict[str, any]:
        """Process document using LlamaIndex PyMuPDFReader (fast)"""
        reader = self._get_pymupdf_reader()

        # Calculate file hash for duplicate detection
        file_hash = self.get_file_hash(file_path)

        # PyMuPDFReader returns list of Document objects
        documents = reader.load_data(file_path)

        # Combine all document text
        text = "\n\n".join([doc.text for doc in documents])

        # Get page count from metadata if available
        num_pages = len(documents) if documents else 0

        metadata = {
            "page_count": num_pages,
            "source": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "file_hash": file_hash,  # For duplicate detection
            "processor": "pymupdf"
        }

        print(f"✓ PyMuPDF: Extracted {len(text)} characters from {num_pages} pages")
        print(f"  File hash: {file_hash}")

        return {
            "text": text,
            "pages": num_pages,
            "file_path": file_path,
            "metadata": metadata
        }

    def batch_process_documents(
        self,
        gcs_uris: List[str],
        cache_dir: str = "./data/cache"
    ) -> List[Dict]:
        """
        Process multiple documents in batch.

        Args:
            gcs_uris: List of GCS URIs
            cache_dir: Local cache directory

        Returns:
            List of processed document dictionaries
        """
        results = []

        for i, gcs_uri in enumerate(gcs_uris, 1):
            print(f"\n[{i}/{len(gcs_uris)}] Processing: {gcs_uri}")

            try:
                result = self.process_gcs_document(gcs_uri, cache_dir)
                results.append(result)
                print(f"✓ Success")
            except Exception as e:
                print(f"✗ Failed: {e}")
                results.append({
                    "gcs_uri": gcs_uri,
                    "error": str(e),
                    "text": None
                })

        print(f"\n{'='*60}")
        print(f"Batch processing complete:")
        print(f"  Total: {len(gcs_uris)}")
        print(f"  Success: {len([r for r in results if r.get('text')])}")
        print(f"  Failed: {len([r for r in results if not r.get('text')])}")
        print(f"{'='*60}")

        return results


def download_from_gcs(gcs_uri: str, local_path: str) -> str:
    """
    Download a file from GCS to local path.

    Args:
        gcs_uri: GCS URI (gs://bucket/path/file.pdf)
        local_path: Local destination path

    Returns:
        Local file path
    """
    # Parse GCS URI
    parts = gcs_uri.replace("gs://", "").split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1] if len(parts) > 1 else ""

    # Download file
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.download_to_filename(local_path)

    return local_path


def process_directory(
    directory: str,
    pattern: str = "*.pdf"
) -> List[Dict]:
    """
    Process all PDFs in a local directory.

    Args:
        directory: Path to directory
        pattern: File pattern (default: *.pdf)

    Returns:
        List of processed documents
    """
    processor = DocumentProcessor()

    pdf_files = list(Path(directory).glob(pattern))
    print(f"Found {len(pdf_files)} PDF files in {directory}")

    results = []
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")

        try:
            result = processor.process_local_document(str(pdf_path))
            results.append(result)
        except Exception as e:
            print(f"✗ Failed: {e}")
            results.append({
                "file_path": str(pdf_path),
                "error": str(e),
                "text": None
            })

    return results


# Example usage
if __name__ == "__main__":
    processor = DocumentProcessor()

    # Example 1: Process local PDF
    result = processor.process_local_document("./data/manuals/sample_manual.pdf")
    print(f"\nExtracted {len(result['text'])} characters")
    print(f"Pages: {result['pages']}")
    print(f"First 200 chars: {result['text'][:200]}...")

    # Example 2: Process from GCS
    # result = processor.process_gcs_document(
    #     "gs://your-bucket/manuals/samsung_rf28.pdf"
    # )

    # Example 3: Process directory
    # results = process_directory("./data/manuals/")
