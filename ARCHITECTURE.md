# Home Appliance Assistant - System Architecture

> **Personalized AI assistant for home appliance troubleshooting, maintenance, and manual management**

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Data Architecture](#data-architecture)
4. [Ingestion Pipeline](#ingestion-pipeline)
5. [Search & Retrieval](#search--retrieval)
6. [Agent System](#agent-system)
7. [API Layer](#api-layer)
8. [Infrastructure](#infrastructure)
9. [Security & Privacy](#security--privacy)
10. [Scalability](#scalability)

---

## System Overview

### Core Capabilities

**User Onboarding:**
- User provides list of home appliances (brand, model)
- System auto-discovers and downloads manuals from web
- Creates personalized appliance library

**Intelligent Troubleshooting:**
- User describes appliance issue
- AI identifies which appliance and retrieves relevant manual sections
- Provides step-by-step troubleshooting guidance
- Checks safety constraints
- Creates service tickets if needed

**Proactive Maintenance:**
- Tracks maintenance schedules per appliance
- Sends reminders (filter changes, cleaning, etc.)
- Monitors recalls and safety alerts
- Maintains service history

### Key Differentiators

✅ **Multi-appliance support** (refrigerators, washers, dryers, dishwashers, etc.)
✅ **Auto-discovery** of manuals from manufacturer websites
✅ **User-specific** context (only search user's owned appliances)
✅ **Instance-level tracking** (specific serial numbers, purchase dates, warranties)
✅ **Hybrid processing** (<20MB Docling, ≥20MB PyMuPDF for 275x speedup)
✅ **Smart deduplication** (file hash, content hash, semantic similarity)
✅ **Scalable** to 100,000+ manuals and millions of users

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            USER INTERFACE                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Web App      │  │ Mobile App   │  │ Voice (Alexa)│  │ Smart Home   ││
│  │ (React)      │  │ (iOS/Android)│  │ (Google Home)│  │ Integration  ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Authentication │ Rate Limiting │ Request Routing │ Logging       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
        ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
        │  USER SERVICE    │ │ APPLIANCE    │ │ TROUBLESHOOTING  │
        │                  │ │ SERVICE      │ │ SERVICE          │
        │ - User CRUD      │ │ - Inventory  │ │ - RAG Search     │
        │ - Homes          │ │ - Onboarding │ │ - Agent System   │
        │ - Preferences    │ │ - Maintenance│ │ - Tickets        │
        └──────────────────┘ └──────────────┘ └──────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ PostgreSQL  │  │   Qdrant    │  │     GCS     │  │    Redis    │  │
│  │             │  │             │  │             │  │             │  │
│  │ - Users     │  │ - Vectors   │  │ - PDF Files │  │ - Cache     │  │
│  │ - Appliances│  │ - Chunks    │  │ - Images    │  │ - Sessions  │  │
│  │ - Service   │  │ - Metadata  │  │ - Logs      │  │ - Queues    │  │
│  │ - Tickets   │  │             │  │             │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKGROUND PROCESSING                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    INGESTION PIPELINE                             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │  │
│  │  │ Web Scraper│→ │ Processor  │→ │ Chunker    │→ │ Embedder   │ │  │
│  │  │ (Scrapy)   │  │(Docling/   │  │(LlamaIndex)│  │ (OpenAI)   │ │  │
│  │  │            │  │ PyMuPDF)   │  │            │  │            │ │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │  │
│  │         │               │               │               │         │  │
│  │         └───────────────┴───────────────┴───────────────┘         │  │
│  │                            ▼                                       │  │
│  │                  ┌─────────────────────┐                          │  │
│  │                  │  Metadata Extractor │                          │  │
│  │                  │  (Gemini LLM)       │                          │  │
│  │                  └─────────────────────┘                          │  │
│  │                            ▼                                       │  │
│  │                  ┌─────────────────────┐                          │  │
│  │                  │ Deduplication Check │                          │  │
│  │                  │ (Multi-level)       │                          │  │
│  │                  └─────────────────────┘                          │  │
│  │                            ▼                                       │  │
│  │                  ┌─────────────────────┐                          │  │
│  │                  │  Store in Qdrant    │                          │  │
│  │                  └─────────────────────┘                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    BACKGROUND JOBS                                │  │
│  │  - Recall monitoring                                              │  │
│  │  - Maintenance reminders                                          │  │
│  │  - Manual updates check                                           │  │
│  │  - Analytics/reporting                                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL INTEGRATIONS                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Manufacturer │  │ Recall APIs  │  │ Parts        │  │ Service      ││
│  │ Websites     │  │ (CPSC)       │  │ Suppliers    │  │ Providers    ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Architecture

### 1. PostgreSQL (Relational Data)

**Users Table**
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    preferences JSONB,
    status VARCHAR(50) DEFAULT 'active'
);

CREATE INDEX idx_users_email ON users(email);
```

**Homes Table**
```sql
CREATE TABLE homes (
    home_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    name VARCHAR(255),
    address JSONB,  -- {street, city, state, zip, country}
    timezone VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_homes_user ON homes(user_id);
```

**Appliances Table** (Instance-level)
```sql
CREATE TABLE appliances (
    instance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    home_id UUID REFERENCES homes(home_id),

    -- Identification
    brand VARCHAR(100) NOT NULL,
    appliance_category VARCHAR(100) NOT NULL,
    appliance_subcategory VARCHAR(100),
    model_number VARCHAR(100) NOT NULL,
    model_name VARCHAR(255),
    serial_number VARCHAR(100),
    sku VARCHAR(100),

    -- User customization
    nickname VARCHAR(255),
    location VARCHAR(255),  -- "Kitchen", "Laundry Room"

    -- Ownership
    purchase_date DATE,
    purchase_price DECIMAL(10,2),
    retailer VARCHAR(255),

    -- Warranty
    warranty_start DATE,
    warranty_end DATE,
    warranty_type VARCHAR(50),

    -- Installation
    installation_date DATE,
    installer VARCHAR(255),

    -- Lifecycle
    status VARCHAR(50) DEFAULT 'active',  -- active, storage, disposed, sold

    -- Features & specs
    features JSONB,  -- ["ice_maker", "wifi_enabled"]
    specifications JSONB,  -- {capacity: "28 cu ft", voltage: "115V"}

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_appliances_user ON appliances(user_id);
CREATE INDEX idx_appliances_category ON appliances(appliance_category);
CREATE INDEX idx_appliances_model ON appliances(model_number);
```

**Manuals Table**
```sql
CREATE TABLE manuals (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What it applies to
    model_numbers TEXT[],  -- Array of compatible models
    brand VARCHAR(100),
    appliance_category VARCHAR(100),

    -- Manual info
    manual_type VARCHAR(50),  -- user, service, installation, parts
    language VARCHAR(10),
    version VARCHAR(50),
    year INTEGER,
    region VARCHAR(50),

    -- File info
    file_name VARCHAR(500),
    file_hash VARCHAR(64) UNIQUE,  -- MD5 for exact duplicate detection
    content_hash VARCHAR(64),      -- Normalized content hash
    file_size BIGINT,
    page_count INTEGER,

    -- Storage
    gcs_uri TEXT,
    storage_path TEXT,

    -- Source
    source_type VARCHAR(100),  -- manufacturer, retailer, manual_archive
    source_url TEXT,
    download_url TEXT,
    download_date TIMESTAMP,

    -- Processing
    processor VARCHAR(50),  -- docling, pymupdf
    processing_date TIMESTAMP,
    indexed BOOLEAN DEFAULT FALSE,
    chunk_count INTEGER,

    -- Metadata
    metadata JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_manuals_model ON manuals USING GIN(model_numbers);
CREATE INDEX idx_manuals_hash ON manuals(file_hash);
CREATE INDEX idx_manuals_content ON manuals(content_hash);
CREATE INDEX idx_manuals_category ON manuals(appliance_category);
```

**Appliance_Manuals (Junction Table)**
```sql
CREATE TABLE appliance_manuals (
    appliance_id UUID REFERENCES appliances(instance_id),
    manual_id UUID REFERENCES manuals(document_id),
    linked_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (appliance_id, manual_id)
);
```

**Service Events Table**
```sql
CREATE TABLE service_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appliance_id UUID REFERENCES appliances(instance_id),
    user_id UUID REFERENCES users(user_id),

    event_type VARCHAR(50),  -- repair, maintenance, inspection, recall
    event_date DATE NOT NULL,
    description TEXT,

    -- Service details
    technician VARCHAR(255),
    service_provider VARCHAR(255),
    cost DECIMAL(10,2),
    warranty_covered BOOLEAN,

    -- Parts
    parts_replaced JSONB,  -- [{part: "ice_maker", part_number: "DA97-..."}]

    notes TEXT,
    attachments JSONB,  -- [{type: "invoice", url: "gs://..."}]

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_service_appliance ON service_events(appliance_id);
CREATE INDEX idx_service_date ON service_events(event_date);
```

**Maintenance Schedules Table**
```sql
CREATE TABLE maintenance_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appliance_id UUID REFERENCES appliances(instance_id),

    task_name VARCHAR(255),
    description TEXT,
    frequency_months INTEGER,

    last_performed DATE,
    next_due DATE,

    -- Task details
    parts_needed JSONB,  -- [{part: "water_filter", number: "HAF-CIN"}]
    estimated_cost DECIMAL(10,2),
    diy BOOLEAN DEFAULT FALSE,

    -- Reminders
    reminder_enabled BOOLEAN DEFAULT TRUE,
    reminder_days_before INTEGER DEFAULT 7,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_maint_appliance ON maintenance_schedules(appliance_id);
CREATE INDEX idx_maint_next_due ON maintenance_schedules(next_due);
```

**Troubleshooting Sessions Table**
```sql
CREATE TABLE troubleshooting_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    appliance_id UUID REFERENCES appliances(instance_id),

    -- Issue
    issue_summary TEXT,
    symptoms JSONB,  -- ["ice maker not working", "loud noise"]
    error_codes JSONB,  -- ["ER 22", "5E"]

    -- Conversation
    conversation JSONB,  -- [{role: "user", content: "..."}, {role: "assistant", ...}]

    -- Resolution
    status VARCHAR(50),  -- in_progress, resolved, escalated
    resolution TEXT,
    resolved_at TIMESTAMP,

    -- Outcome
    service_ticket_created BOOLEAN DEFAULT FALSE,
    ticket_id UUID,
    user_satisfaction INTEGER,  -- 1-5 rating

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ts_user ON troubleshooting_sessions(user_id);
CREATE INDEX idx_ts_appliance ON troubleshooting_sessions(appliance_id);
CREATE INDEX idx_ts_status ON troubleshooting_sessions(status);
```

**Service Tickets Table**
```sql
CREATE TABLE service_tickets (
    ticket_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    appliance_id UUID REFERENCES appliances(instance_id),
    session_id UUID REFERENCES troubleshooting_sessions(session_id),

    status VARCHAR(50) DEFAULT 'open',  -- open, in_progress, resolved, closed
    priority VARCHAR(50),  -- low, medium, high, urgent

    -- Issue details
    summary TEXT,
    symptoms JSONB,
    error_codes JSONB,
    attempted_steps JSONB,

    -- Assignment
    assigned_to VARCHAR(255),
    assigned_at TIMESTAMP,

    -- Resolution
    resolution TEXT,
    resolved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tickets_user ON service_tickets(user_id);
CREATE INDEX idx_tickets_status ON service_tickets(status);
```

---

### 2. Qdrant (Vector Store)

**Collection Structure:**

```python
collection_config = {
    "collection_name": "appliance_manuals",
    "vectors": {
        "size": 1536,  # OpenAI text-embedding-3-small
        "distance": "Cosine"
    },
    "payload_schema": {
        # User & Appliance Context
        "user_id": "keyword",           # For user-specific search
        "instance_id": "keyword",       # Link to specific appliance
        "home_id": "keyword",

        # Product Identification
        "brand": "keyword",
        "appliance_category": "keyword",
        "appliance_subcategory": "keyword",
        "model_number": "keyword",
        "model_family": "keyword",

        # Manual Information
        "document_id": "keyword",
        "manual_type": "keyword",       # user, service, installation
        "language": "keyword",
        "version": "text",
        "year": "integer",

        # Deduplication
        "file_hash": "keyword",
        "content_hash": "keyword",

        # Document Structure
        "chunk_id": "integer",
        "page_number": "integer",
        "section": "text",              # "Troubleshooting - Ice Maker"

        # Content
        "text": "text",                 # Actual chunk text

        # Processing
        "processor": "keyword",
        "processing_date": "text",

        # Storage
        "gcs_uri": "text",
        "file_name": "text",
    }
}
```

**Payload Indexes** (for fast filtering):
```python
# Create indexes on frequently filtered fields
indexes = [
    "user_id",
    "instance_id",
    "brand",
    "appliance_category",
    "model_number",
    "manual_type",
    "file_hash",
    "document_id"
]
```

---

### 3. Google Cloud Storage (GCS)

**Bucket Structure:**
```
gs://appliance-manuals/
├── raw/                                    # Original downloaded PDFs
│   ├── manufacturer/
│   │   ├── samsung/
│   │   │   ├── refrigerator/
│   │   │   │   └── RF28HMEDBSR_user_v2.pdf
│   │   │   └── washer/
│   │   └── lg/
│   └── user_uploads/
│       └── user_12345/
│           └── custom_manual.pdf
│
├── processed/                              # Cached processed data
│   ├── user_12345/
│   │   └── appliance_abc123/
│   │       ├── user_manual.json          # Extracted text + metadata
│   │       └── chunks.json               # Chunked text
│
├── user_data/                              # User-specific files
│   └── user_12345/
│       ├── photos/                        # Appliance photos
│       ├── receipts/                      # Purchase receipts
│       └── service_reports/               # Service documents
│
└── logs/                                   # System logs
    ├── ingestion/
    ├── search/
    └── errors/
```

---

### 4. Redis (Caching & Queues)

**Cache Keys:**
```python
# User session cache
"session:{session_id}" → {user_id, appliances, context}

# Search result cache (5 min TTL)
"search:{user_id}:{query_hash}" → {results, timestamp}

# Appliance metadata cache (1 hour TTL)
"appliance:{instance_id}" → {full_metadata}

# Manual metadata cache
"manual:{document_id}" → {metadata}

# Rate limiting
"ratelimit:{user_id}:{endpoint}" → request_count
```

**Task Queues:**
```python
# Ingestion queue (Celery/RQ)
"queue:ingestion" → [
    {task: "download_manual", url: "...", user_id: "..."},
    {task: "process_pdf", file_path: "...", instance_id: "..."}
]

# Background jobs queue
"queue:jobs" → [
    {task: "check_recalls", brand: "Samsung", model: "RF28..."},
    {task: "send_maintenance_reminder", user_id: "...", appliance_id: "..."}
]
```

---

## Ingestion Pipeline

### Auto-Discovery & Download Flow

```
User provides appliance list
         │
         ▼
┌────────────────────────┐
│  Appliance Validator   │  ← Validate brand/model exists
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Create Instance       │  ← Store in PostgreSQL
│  (PostgreSQL)          │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Web Scraper           │  ← Search manufacturer site
│  (Scrapy/BeautifulSoup)│     for manual download URLs
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Download PDFs         │  ← Download to GCS raw/
│  (parallel)            │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Deduplication Check   │  ← Check file hash in DB
│  (Multi-level)         │     Skip if duplicate
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Document Processor    │  ← Hybrid: Docling or PyMuPDF
│  (Size-based routing)  │     based on file size (20MB)
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Metadata Extractor    │  ← LLM extracts metadata from
│  (Gemini Flash)        │     first page (model, type, etc)
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Chunker               │  ← LlamaIndex SentenceSplitter
│  (LlamaIndex)          │     512 tokens, 50 overlap
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Embedder              │  ← OpenAI text-embedding-3-small
│  (OpenAI API)          │     Batch process (100/batch)
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Store Vectors         │  ← Qdrant with full metadata
│  (Qdrant)              │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Link to Appliance     │  ← Update appliance_manuals table
│  (PostgreSQL)          │
└────────────────────────┘
         │
         ▼
┌────────────────────────┐
│  Background Jobs       │  ← Check recalls, set up
│  (Celery)              │     maintenance schedule
└────────────────────────┘
```

### Deduplication Logic

```python
def check_duplicate(file_path, metadata):
    """Multi-level duplicate detection"""

    # Level 1: File hash (exact duplicate)
    file_hash = calculate_hash(file_path)
    if db.manuals.exists(file_hash=file_hash):
        return {"duplicate": True, "level": "file_hash", "action": "skip"}

    # Level 2: Composite key (same model + type + version)
    key = f"{metadata['brand']}_{metadata['model']}_{metadata['manual_type']}_{metadata['version']}"
    if db.manuals.exists(composite_key=key):
        return {"duplicate": True, "level": "composite_key", "action": "skip"}

    # Level 3: Content hash (same content, different PDF)
    content_hash = calculate_content_hash(extract_text(file_path))
    if db.manuals.exists(content_hash=content_hash):
        return {"duplicate": True, "level": "content_hash", "action": "skip"}

    # Level 4: Semantic similarity (different version check)
    doc_embedding = embed_document(extract_text(file_path))
    similar = vector_store.search_similar_documents(
        embedding=doc_embedding,
        threshold=0.95,
        filters={"model_number": metadata['model']}
    )

    if similar:
        if similar[0]['score'] > 0.98:
            return {"duplicate": True, "level": "semantic", "action": "skip"}
        elif similar[0]['score'] > 0.95:
            return {"duplicate": False, "level": "semantic", "action": "flag_similar", "related": similar}

    return {"duplicate": False, "action": "process"}
```

---

## Search & Retrieval

### User-Specific RAG Pipeline

```python
def search_user_manuals(user_id, query, appliance_id=None):
    """
    RAG search with user-specific context
    """

    # 1. Get user's appliances
    user_appliances = db.appliances.filter(user_id=user_id)

    # 2. Build filter
    filters = {"user_id": user_id}

    if appliance_id:
        filters["instance_id"] = appliance_id
    else:
        # Search across all user's appliances
        filters["instance_id"] = [a.instance_id for a in user_appliances]

    # 3. Embed query
    query_embedding = embedder.embed(query)

    # 4. Search Qdrant
    results = vector_store.search(
        query_vector=query_embedding,
        top_k=5,
        filters=filters
    )

    # 5. Re-rank by relevance + recency
    ranked = rerank_results(results, user_preferences)

    # 6. Return with appliance context
    return {
        "results": ranked,
        "appliances": [get_appliance_context(r) for r in ranked]
    }
```

### Hybrid Search (Keyword + Semantic)

```python
def hybrid_search(user_id, query, appliance_category=None):
    """
    Combine keyword and semantic search
    """

    # Keyword search (for model numbers, error codes)
    keyword_results = db.manuals.search(
        query=query,
        user_id=user_id,
        appliance_category=appliance_category
    )

    # Semantic search (for natural language)
    semantic_results = vector_store.search(
        query=query,
        user_id=user_id,
        appliance_category=appliance_category
    )

    # Merge and deduplicate
    merged = merge_results(keyword_results, semantic_results)

    return merged
```

---

## Agent System

### Sequential Agent Architecture (Google ADK)

```
User Query: "My fridge is making a loud noise and not cooling"
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   CORE ORCHESTRATOR                          │
│  - Executes agents in sequential order                       │
│  - Passes context from one agent to the next                 │
│  - Maintains conversation state                              │
│  - Ensures user-specific filtering                           │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: SYMPTOM EXTRACTOR                                    │
│                                                              │
│ Extracts:                                                    │
│ - Symptoms from user query                                   │
│ - Error codes mentioned                                      │
│ - When issue started                                         │
│ - Severity indicators                                        │
│                                                              │
│ Output: Structured symptom data                              │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: APPLIANCE IDENTIFIER                                 │
│                                                              │
│ Identifies:                                                  │
│ - Which appliance user is referring to                       │
│ - Model number from user's inventory                         │
│ - Warranty status                                            │
│ - Purchase date and age                                      │
│                                                              │
│ Input: Symptom data from Step 1                              │
│ Output: Appliance instance_id and metadata                   │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: RAG RETRIEVER                                        │
│                                                              │
│ Searches:                                                    │
│ - User's manuals for identified appliance                    │
│ - Relevant troubleshooting sections                          │
│ - Error code explanations                                    │
│ - Maintenance procedures                                     │
│                                                              │
│ Input: Appliance ID + symptoms from Steps 1-2                │
│ Output: Top 5 relevant manual sections                       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: TROUBLESHOOTING PLANNER                              │
│                                                              │
│ Creates:                                                     │
│ - Step-by-step troubleshooting plan                          │
│ - Ordered from simple to complex                             │
│ - Expected outcomes per step                                 │
│ - When to escalate to service                                │
│                                                              │
│ Input: Symptoms + appliance data + manual sections           │
│ Output: Structured troubleshooting plan                      │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: SAFETY CHECKER                                       │
│                                                              │
│ Reviews:                                                     │
│ - Checks plan for safety issues                              │
│ - Blocks unsafe steps (electrical, gas, refrigerant)         │
│ - Adds safety warnings                                       │
│ - Validates warranty implications                            │
│                                                              │
│ Input: Troubleshooting plan from Step 4                      │
│ Output: Safety-validated plan with warnings                  │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: RESPONSE FORMATTER                                   │
│                                                              │
│ Formats:                                                     │
│ - User-friendly response                                     │
│ - Adds relevant images/diagrams                              │
│ - Includes safety notes prominently                          │
│ - Suggests follow-up actions                                 │
│                                                              │
│ Input: Safety-validated plan from Step 5                     │
│ Output: Final formatted response to user                     │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: TICKETING AGENT (Conditional)                        │
│                                                              │
│ Creates (if needed):                                         │
│ - Service ticket for professional help                       │
│ - Schedules service appointment                              │
│ - Estimates cost                                             │
│ - Finds qualified technicians                                │
│                                                              │
│ Input: Issue requires professional service                   │
│ Output: Service ticket and appointment details               │
└─────────────────────────────────────────────────────────────┘
```

### Sequential Agent Configurations

**STEP 1: Symptom Extractor Agent**
```python
symptom_extractor_agent = Agent(
    name="symptom_extractor",
    model="gemini-2.5-flash",
    instruction="""
    FIRST STEP in sequential pipeline.
    Extract structured symptom information from user's query.

    Extract and structure:
    1. Primary symptoms (e.g., "loud noise", "not cooling")
    2. Error codes mentioned (e.g., "ER 22", "5E")
    3. Timeline (when issue started, frequency)
    4. Severity indicators (safety concerns, urgency)
    5. Additional context (recent changes, weather, etc.)

    Output format:
    {
        "symptoms": ["loud noise", "not cooling"],
        "error_codes": [],
        "timeline": "started yesterday",
        "severity": "medium",
        "context": "after power outage"
    }

    This output will be passed to the next agent (Appliance Identifier).
    """,
    tools=[]
)
```

**STEP 2: Appliance Identifier Agent**
```python
appliance_identifier_agent = Agent(
    name="appliance_identifier",
    model="gemini-2.5-flash",
    instruction="""
    SECOND STEP in sequential pipeline.
    Receives: Symptom data from Step 1

    Identify which appliance the user is asking about.

    1. Check user's appliance inventory (provided in context)
    2. Match based on:
       - Explicit mention ("my Samsung fridge")
       - Location ("kitchen refrigerator")
       - Nickname ("main fridge")
       - Type + symptoms (only one fridge → must be that one)
    3. If ambiguous, ask user to clarify
    4. Retrieve appliance details (model, warranty, age)

    Output format:
    {
        "instance_id": "uuid",
        "brand": "Samsung",
        "model_number": "RF28HMEDBSR",
        "warranty_status": "active",
        "age_years": 2
    }

    This output will be passed to the next agent (RAG Retriever).
    """,
    tools=[get_user_appliances]
)
```

**STEP 3: RAG Retrieval Agent**
```python
rag_retrieval_agent = Agent(
    name="rag_retrieval",
    model="gemini-2.5-flash",
    instruction="""
    THIRD STEP in sequential pipeline.
    Receives: Symptoms (Step 1) + Appliance ID (Step 2)

    Search the user's appliance manuals for relevant information.

    IMPORTANT:
    - Only search manuals for the identified appliance (instance_id)
    - Use the user_id to ensure user-specific filtering
    - Search using symptoms and error codes from Step 1
    - Focus on troubleshooting sections, error code explanations
    - Return top 5 most relevant sections with page numbers

    Output format:
    {
        "relevant_sections": [
            {
                "section": "Troubleshooting - Ice Maker",
                "content": "...",
                "page": 42,
                "relevance_score": 0.95
            }
        ]
    }

    This output will be passed to the next agent (Troubleshooting Planner).
    """,
    tools=[search_user_manuals]
)
```

**STEP 4: Troubleshooting Planner Agent**
```python
troubleshooting_planner = Agent(
    name="troubleshooting_planner",
    model="gemini-2.5-flash",
    instruction="""
    FOURTH STEP in sequential pipeline.
    Receives: Symptoms (Step 1) + Appliance data (Step 2) + Manual sections (Step 3)

    Create step-by-step troubleshooting plan from manual sections.

    1. Analyze symptoms and manual recommendations
    2. Order steps from simple to complex (easy checks first)
    3. Include for each step:
       - Clear instructions
       - Expected outcome
       - When to stop (if resolved)
       - Estimated time
    4. Check warranty status - if under warranty, suggest service early
    5. Identify if issue requires professional service

    Output format:
    {
        "steps": [
            {
                "step_number": 1,
                "action": "Check if refrigerator is plugged in",
                "expected_outcome": "Power light should be on",
                "if_resolved": "Issue was power supply",
                "estimated_time": "1 minute"
            }
        ],
        "requires_service": false,
        "warranty_covered": true
    }

    ⚠️ If issue requires professional service, set requires_service=true

    This output will be passed to the next agent (Safety Checker).
    """,
    tools=[get_appliance_warranty]
)
```

**STEP 5: Safety Checker Agent**
```python
safety_checker = Agent(
    name="safety_checker",
    model="gemini-2.5-flash",
    instruction="""
    FIFTH STEP in sequential pipeline.
    Receives: Troubleshooting plan from Step 4

    Review troubleshooting plan for safety issues.

    Block any steps involving:
    - Electrical work beyond unplugging
    - Gas line disconnection
    - Refrigerant handling
    - Removing safety guards
    - Accessing internal components

    Add warnings for:
    - Unplugging before service
    - Water shutoff before plumbing work
    - Heavy appliance tipping hazards
    - Risk of electrical shock

    Output format:
    {
        "safe": true/false,
        "blocked_steps": [2, 5],
        "warnings": [
            "⚠️ Always unplug appliance before inspection",
            "⚠️ Do not attempt to access refrigerant lines"
        ],
        "modified_plan": {...}
    }

    This output will be passed to the next agent (Response Formatter).
    """,
    tools=[check_safety_policy]
)
```

**STEP 6: Response Formatter Agent**
```python
response_formatter = Agent(
    name="response_formatter",
    model="gemini-2.5-flash",
    instruction="""
    SIXTH STEP in sequential pipeline.
    Receives: Safety-validated plan from Step 5

    Format the final response for the user.

    1. Create user-friendly formatting
    2. Add relevant images/diagrams from manual
    3. Highlight safety warnings prominently
    4. Include appliance context (model, warranty)
    5. Suggest next steps or follow-up actions
    6. Provide service contact if needed

    Output format:
    A complete user response with:
    - Summary of issue
    - Step-by-step instructions
    - Safety warnings (highlighted)
    - Visual aids
    - Contact information if service needed

    This output is the FINAL response sent to the user.
    """,
    tools=[get_manual_images, format_markdown]
)
```

**STEP 7: Ticketing Agent (Conditional)**
```python
ticketing_agent = Agent(
    name="ticketing_agent",
    model="gemini-2.5-flash",
    instruction="""
    SEVENTH STEP in sequential pipeline (CONDITIONAL).
    Receives: Signal that professional service is required

    Only executes if troubleshooting plan indicates service needed.

    Create service ticket and schedule appointment:
    1. Gather issue details from previous steps
    2. Create service ticket in database
    3. Find qualified technicians in user's area
    4. Estimate cost based on warranty status
    5. Provide scheduling options

    Output format:
    {
        "ticket_id": "uuid",
        "estimated_cost": "$150-200",
        "warranty_covered": true,
        "available_technicians": [...],
        "next_available": "2024-01-15 10:00 AM"
    }

    This is the FINAL step in the sequential pipeline.
    """,
    tools=[create_service_ticket, find_technicians, estimate_cost]
)
```

### Sequential Execution Flow

```python
def execute_sequential_pipeline(user_query, user_id):
    """
    Execute agents in strict sequential order.
    Each agent receives output from previous agents.
    """

    # Initialize context
    context = {
        "user_query": user_query,
        "user_id": user_id
    }

    # STEP 1: Extract symptoms
    symptoms = symptom_extractor_agent.run(context)
    context["symptoms"] = symptoms

    # STEP 2: Identify appliance
    appliance = appliance_identifier_agent.run(context)
    context["appliance"] = appliance

    # STEP 3: Retrieve relevant manual sections
    manual_sections = rag_retrieval_agent.run(context)
    context["manual_sections"] = manual_sections

    # STEP 4: Create troubleshooting plan
    plan = troubleshooting_planner.run(context)
    context["plan"] = plan

    # STEP 5: Safety check the plan
    safe_plan = safety_checker.run(context)
    context["safe_plan"] = safe_plan

    # STEP 6: Format response
    response = response_formatter.run(context)

    # STEP 7: Create ticket if needed (conditional)
    if context["plan"]["requires_service"]:
        ticket = ticketing_agent.run(context)
        response["ticket"] = ticket

    return response
```

---

## API Layer

### REST API Endpoints (FastAPI)

**Authentication**
```python
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

**User & Home Management**
```python
GET    /api/v1/users/{user_id}
PUT    /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}

POST   /api/v1/users/{user_id}/homes
GET    /api/v1/users/{user_id}/homes
PUT    /api/v1/homes/{home_id}
DELETE /api/v1/homes/{home_id}
```

**Appliance Management**
```python
# Onboarding: Add appliances
POST   /api/v1/appliances/onboard
{
    "user_id": "...",
    "appliances": [
        {"brand": "Samsung", "model": "RF28HMEDBSR", "location": "Kitchen"},
        {"brand": "LG", "model": "WM9000HVA", "location": "Laundry"}
    ]
}

# CRUD
GET    /api/v1/users/{user_id}/appliances
POST   /api/v1/appliances
GET    /api/v1/appliances/{instance_id}
PUT    /api/v1/appliances/{instance_id}
DELETE /api/v1/appliances/{instance_id}

# Manuals
GET    /api/v1/appliances/{instance_id}/manuals
POST   /api/v1/appliances/{instance_id}/manuals/upload
```

**Search & Troubleshooting**
```python
# Search user's manuals
POST   /api/v1/search
{
    "user_id": "...",
    "query": "ice maker not working",
    "appliance_id": "...",  # Optional: filter to specific appliance
    "top_k": 5
}

# Start troubleshooting session
POST   /api/v1/troubleshooting/start
{
    "user_id": "...",
    "appliance_id": "...",
    "issue": "Fridge making loud noise"
}

# Continue conversation
POST   /api/v1/troubleshooting/{session_id}/message
{
    "message": "It's a grinding sound from the freezer"
}

# Get session history
GET    /api/v1/troubleshooting/{session_id}
```

**Maintenance & Service**
```python
# Maintenance schedule
GET    /api/v1/appliances/{instance_id}/maintenance
POST   /api/v1/appliances/{instance_id}/maintenance
PUT    /api/v1/maintenance/{schedule_id}

# Log service event
POST   /api/v1/appliances/{instance_id}/service
GET    /api/v1/appliances/{instance_id}/service

# Create service ticket
POST   /api/v1/tickets
GET    /api/v1/users/{user_id}/tickets
GET    /api/v1/tickets/{ticket_id}
PUT    /api/v1/tickets/{ticket_id}
```

**Recalls & Alerts**
```python
# Check recalls for user's appliances
GET    /api/v1/users/{user_id}/recalls

# Check recalls for specific appliance
GET    /api/v1/appliances/{instance_id}/recalls
```

---

## Infrastructure

### Cloud Architecture (Google Cloud Platform)

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD LOAD BALANCER                       │
│  - SSL Termination                                           │
│  - DDoS Protection                                           │
│  - Global Anycast                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               GOOGLE KUBERNETES ENGINE (GKE)                 │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │  API Pods          │  │  Worker Pods       │            │
│  │  (FastAPI)         │  │  (Celery)          │            │
│  │  - Auto-scaling    │  │  - Ingestion       │            │
│  │  - 3+ replicas     │  │  - Background jobs │            │
│  └────────────────────┘  └────────────────────┘            │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │  ADK Agent Pods    │  │  Scraper Pods      │            │
│  │  (Google ADK)      │  │  (Scrapy)          │            │
│  │  - Troubleshooting │  │  - Web scraping    │            │
│  └────────────────────┘  └────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
│ Cloud SQL        │ │ Memorystore  │ │ Cloud Storage│
│ (PostgreSQL)     │ │ (Redis)      │ │ (GCS)        │
│                  │ │              │ │              │
│ - Multi-AZ       │ │ - HA setup   │ │ - Multi-      │
│ - Auto backup    │ │ - 5GB cache  │ │   region      │
│ - Read replicas  │ │              │ │ - Versioning │
└──────────────────┘ └──────────────┘ └──────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 QDRANT (Self-hosted on GKE)                  │
│  - Persistent disk (SSD)                                     │
│  - Snapshot backups                                          │
│  - Horizontal scaling                                        │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Strategy

**Development Environment**
- Local Docker Compose
- Sample dataset (100 manuals)
- Mocked external APIs

**Staging Environment**
- GKE cluster (3 nodes)
- Cloud SQL (db-n1-standard-2)
- 10K manuals
- Integration tests

**Production Environment**
- GKE cluster (5+ nodes, auto-scaling)
- Cloud SQL (db-n1-standard-4 with read replicas)
- Redis (5GB Memorystore)
- 100K+ manuals
- Multi-region GCS

### Monitoring & Observability

**Metrics (Prometheus + Grafana)**
- Request latency (p50, p95, p99)
- Throughput (requests/sec)
- Error rates
- Ingestion speed (docs/hour)
- Vector search latency
- Cache hit rate

**Logging (Cloud Logging)**
- Application logs
- Audit logs (user actions)
- Error logs with stack traces
- Slow query logs

**Alerting**
- High error rate (>1%)
- High latency (p95 >2s)
- Ingestion failures
- Database connection issues
- Disk space warnings

**Tracing (Cloud Trace)**
- End-to-end request tracing
- Agent execution traces
- Database query traces

---

## Security & Privacy

### Authentication & Authorization

**User Authentication**
- OAuth 2.0 / OpenID Connect
- Support: Google, Apple, Email/Password
- JWT tokens (short-lived access, long-lived refresh)
- MFA support (optional)

**Authorization**
- Role-based access control (RBAC)
- User can only access their own appliances
- Service technicians can be granted temporary access
- Admin role for platform management

**Data Isolation**
- Row-level security in PostgreSQL
- User-specific filtering in Qdrant
- Separate GCS folders per user

### Data Privacy

**PII Handling**
- Encrypt PII at rest (AES-256)
- Encrypt in transit (TLS 1.3)
- Hash sensitive data (serial numbers)
- Anonymize analytics data

**Compliance**
- GDPR compliant (EU users)
- CCPA compliant (CA users)
- Data retention policies
- Right to deletion

**API Security**
- Rate limiting (per user, per IP)
- Input validation & sanitization
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)
- CORS policies

---

## Scalability

### Horizontal Scaling

**API Layer**
- Stateless design (scale to N pods)
- Session state in Redis
- Load balancing with affinity

**Ingestion Pipeline**
- Queue-based processing (Celery)
- Worker auto-scaling based on queue depth
- Parallel processing (50-100 workers)

**Database**
- PostgreSQL read replicas (2-3)
- Connection pooling (PgBouncer)
- Partitioning by user_id for large tables

**Vector Store (Qdrant)**
- Sharding by collection
- Replication for HA
- Separate collections per appliance category (optional)

### Performance Optimization

**Caching Strategy**
```python
# L1: In-memory cache (application)
# L2: Redis (shared cache)
# L3: Database

# Cache hierarchy
def get_appliance(instance_id):
    # L1: Check local cache
    if instance_id in local_cache:
        return local_cache[instance_id]

    # L2: Check Redis
    cached = redis.get(f"appliance:{instance_id}")
    if cached:
        local_cache[instance_id] = cached
        return cached

    # L3: Database
    appliance = db.appliances.get(instance_id)
    redis.setex(f"appliance:{instance_id}", 3600, appliance)
    local_cache[instance_id] = appliance
    return appliance
```

**Database Optimization**
- Indexes on all foreign keys
- Composite indexes for common queries
- Materialized views for analytics
- Batch inserts for vectors

**Vector Search Optimization**
- HNSW indexing (Qdrant)
- Pre-filtering with metadata
- Result caching (5 min TTL)
- Batch embedding (100 chunks/batch)

### Cost Optimization

**Estimated Monthly Costs (Production)**

```
Infrastructure:
- GKE cluster (5 nodes, n1-standard-4):   $500
- Cloud SQL (db-n1-standard-4 + replicas): $400
- Memorystore Redis (5GB):                 $100
- GCS (1TB):                               $20
- Load Balancer:                           $20
- Qdrant (self-hosted on GKE):            included

API Costs:
- OpenAI Embeddings (1M chunks/month):    $100
- Gemini API (100K requests/month):       $50

Total: ~$1,190/month

Per User (1000 users): ~$1.19/month
```

**Cost Reduction Strategies**
- Committed use discounts (30% savings)
- Spot instances for workers (60% savings)
- Batch embedding (reduce API calls)
- Intelligent caching (reduce DB queries)
- Manual cleanup (delete old sessions)

---

## Next Steps for Implementation

### Phase 1: MVP (Weeks 1-4)
- [x] Hybrid document processor (Docling + PyMuPDF)
- [ ] Basic web scraper (1-2 manufacturers)
- [ ] PostgreSQL schema setup
- [ ] Qdrant collection with user filtering
- [ ] Basic API (onboarding, search)
- [ ] Simple agent system (ADK)
- [ ] Single user testing

### Phase 2: Multi-User (Weeks 5-8)
- [ ] User authentication
- [ ] User-specific filtering
- [ ] Multi-appliance support
- [ ] Maintenance tracking
- [ ] Service ticket system
- [ ] 10-user beta test

### Phase 3: Scale (Weeks 9-12)
- [ ] Background job system (Celery)
- [ ] Recall monitoring
- [ ] Auto-download for 10+ manufacturers
- [ ] Performance optimization
- [ ] 100+ user test
- [ ] Analytics dashboard

### Phase 4: Production (Weeks 13-16)
- [ ] Deploy to GKE
- [ ] Monitoring & alerting
- [ ] Load testing (1000 concurrent users)
- [ ] Security audit
- [ ] Public launch

---

## Conclusion

This architecture supports:
✅ **100,000+ manuals** across all appliance types
✅ **Millions of users** with personalized libraries
✅ **Auto-discovery** of manuals from web
✅ **Intelligent deduplication** (4-level strategy)
✅ **Fast processing** (275x speedup with hybrid approach)
✅ **User-specific search** (only user's appliances)
✅ **Multi-agent troubleshooting** (Google ADK)
✅ **Proactive maintenance** (reminders, recalls)
✅ **Scalable infrastructure** (Kubernetes, auto-scaling)
✅ **Cost-effective** (~$1.19/user/month at scale)

Ready to build! 🚀
