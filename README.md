# Fridge Troubleshooting - RAG System

AI-powered Samsung refrigerator troubleshooting system using **Retrieval-Augmented Generation (RAG)** with Google ADK agents.

## Overview

This is an alternative implementation of the fridge troubleshooting system using a custom RAG pipeline instead of Google File Search.

### Tech Stack

- **Document Source**: Google Cloud Storage (GCS)
- **Text Extraction**: Docling (open-source, local processing)
- **Chunking**: LlamaIndex
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Vector Store**: Qdrant
- **Agents**: Google ADK (Agent Development Kit)
- **LLM**: Gemini 2.5 Flash

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE                              │
└─────────────────────────────────────────────────────────────┘

1. Document Ingestion
   ┌─────────────┐
   │ GCS Bucket  │ (PDF manuals)
   └──────┬──────┘
          │
          ↓
   ┌─────────────┐
   │ Document AI │ (Text extraction)
   └──────┬──────┘
          │
          ↓
   ┌─────────────┐
   │ LlamaIndex  │ (Chunking)
   └──────┬──────┘
          │
          ↓
   ┌─────────────┐
   │ OpenAI      │ (Embeddings)
   └──────┬──────┘
          │
          ↓
   ┌─────────────┐
   │ Qdrant      │ (Vector storage)
   └─────────────┘

2. Query Processing
   User Query
      ↓
   Embed Query (OpenAI)
      ↓
   Vector Search (Qdrant)
      ↓
   Retrieve Context
      ↓
   ADK Agents (Gemini)
      ↓
   Response
```

## Project Structure

```
fridge_troubleshooting_rag/
├── rag_pipeline/
│   ├── __init__.py
│   ├── document_processor.py    # GCS + Document AI
│   ├── chunking.py              # LlamaIndex chunking
│   ├── embedding.py             # OpenAI embeddings
│   ├── vector_store.py          # Qdrant operations
│   └── retriever.py             # Query retrieval
│
├── agents/
│   ├── __init__.py
│   ├── core_orchestrator.py     # Main agent
│   ├── symptom_extractor.py     # Extract symptoms
│   ├── rag_retrieval_agent.py   # RAG retrieval (replaces file_search_tool)
│   ├── troubleshooting_planner.py
│   ├── safety_checker.py
│   ├── ticketing_agent.py
│   ├── session_manager.py
│   └── sentiment_agent.py
│
├── config/
│   └── policy_safety.yaml       # Safety policies
│
├── data/
│   └── manuals/                 # Local manual cache (optional)
│
├── scripts/
│   ├── ingest_manuals.py        # Bulk ingestion script
│   └── setup_qdrant.py          # Initialize Qdrant
│
├── .env.example                 # Environment template
├── requirements.txt             # Dependencies
├── README.md                    # This file
└── adk.yaml                     # ADK configuration
```

## Setup

### 1. Install Dependencies

```bash
cd fridge_troubleshooting_rag
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Start Qdrant (Local)

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or using docker-compose (create docker-compose.yml)
docker-compose up -d
```

### 4. Ingest Manuals

```bash
# Initialize Qdrant collection
python scripts/setup_qdrant.py

# Ingest manuals from GCS
python scripts/ingest_manuals.py
```

### 5. Run the Agent

```bash
google-adk start
```

## Key Differences from File Search Version

| Aspect | File Search | RAG (This Project) |
|--------|-------------|-------------------|
| **Text Extraction** | Automatic (Google) | Document AI |
| **Chunking** | Automatic (Google) | LlamaIndex (custom) |
| **Embeddings** | Automatic (Google) | OpenAI (explicit) |
| **Vector Store** | Google-managed | Qdrant (self-hosted) |
| **Control** | Low | High |
| **Cost** | Query-based | Storage + Embedding + Query |
| **Customization** | Limited | Full control |

## Advantages of RAG Approach

✅ **Full control** over chunking strategy
✅ **Customize** chunk sizes and overlap
✅ **Choose** embedding model (OpenAI, Cohere, etc.)
✅ **Self-host** vector store (Qdrant locally)
✅ **Optimize** for specific use cases
✅ **Debug** each pipeline stage
✅ **Cost optimization** opportunities

## Usage

### Ingest a New Manual

```python
from rag_pipeline.document_processor import DocumentProcessor
from rag_pipeline.chunking import chunk_documents
from rag_pipeline.embedding import embed_chunks
from rag_pipeline.vector_store import QdrantStore

# Process document
processor = DocumentProcessor()
text = processor.process_gcs_document("gs://bucket/manual.pdf")

# Chunk
chunks = chunk_documents(text, chunk_size=512, overlap=50)

# Embed
embeddings = embed_chunks(chunks)

# Store
store = QdrantStore()
store.add_documents(chunks, embeddings)
```

### Query the System

```python
from agents.core_orchestrator import create_core_orchestrator

agent = create_core_orchestrator()
response = agent.run("My ice maker is not working")
print(response)
```

## Monitoring

### Qdrant Dashboard
- Local: http://localhost:6333/dashboard
- Check collection stats, vector count, etc.

### ADK Logs
```bash
tail -f logs/adk.log
```

## Troubleshooting

### Qdrant Connection Issues
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# Restart Qdrant
docker restart qdrant
```

### Document AI Quota
- Check quota: https://console.cloud.google.com/apis/api/documentai.googleapis.com/quotas
- Increase if needed

### Embedding Rate Limits
- OpenAI: 3,000 RPM for tier 1
- Use batching in scripts/ingest_manuals.py

## Next Steps

1. ✅ Set up environment
2. ✅ Start Qdrant
3. ✅ Ingest sample manual
4. ✅ Test retrieval
5. ✅ Run full agent
6. Compare with File Search version

## Resources

- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Document AI Docs](https://cloud.google.com/document-ai/docs)
- [Google ADK Docs](https://developers.google.com/adk)
