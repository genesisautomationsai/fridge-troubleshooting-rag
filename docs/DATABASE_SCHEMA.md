# Database Schema - Detailed Design

## Entity Relationship Diagram (ERD)

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USERS & HOMES                                 │
└──────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐
    │      USERS          │
    ├─────────────────────┤
    │ PK user_id          │──┐
    │    email            │  │
    │    name             │  │
    │    phone            │  │
    │    created_at       │  │
    │    preferences      │  │
    │    status           │  │
    └─────────────────────┘  │
                             │
                             │ 1:N
                             │
    ┌─────────────────────┐  │
    │      HOMES          │  │
    ├─────────────────────┤  │
    │ PK home_id          │  │
    │ FK user_id          │←─┘
    │    name             │
    │    address (JSONB)  │
    │    timezone         │
    │    created_at       │
    └─────────────────────┘
            │
            │ 1:N
            │
            ▼

┌──────────────────────────────────────────────────────────────────────┐
│                          APPLIANCES                                  │
└──────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────┐
    │      APPLIANCES             │
    ├─────────────────────────────┤
    │ PK instance_id              │──┐
    │ FK user_id                  │  │
    │ FK home_id                  │  │
    │    brand                    │  │
    │    appliance_category       │  │
    │    appliance_subcategory    │  │
    │    model_number             │  │
    │    model_name               │  │
    │    serial_number            │  │
    │    nickname                 │  │
    │    location                 │  │
    │    purchase_date            │  │
    │    warranty_start           │  │
    │    warranty_end             │  │
    │    features (JSONB)         │  │
    │    specifications (JSONB)   │  │
    │    status                   │  │
    └─────────────────────────────┘  │
            │                        │
            │ M:N                    │
            │                        │
            ▼                        │
    ┌─────────────────────────────┐  │
    │  APPLIANCE_MANUALS          │  │
    │  (Junction Table)           │  │
    ├─────────────────────────────┤  │
    │ FK appliance_id             │←─┘
    │ FK manual_id                │──┐
    │    linked_at                │  │
    └─────────────────────────────┘  │
                                     │
                                     │
┌──────────────────────────────────────────────────────────────────────┐
│                          MANUALS                                     │
└──────────────────────────────────────────────────────────────────────┘
                                     │
    ┌─────────────────────────────┐  │
    │      MANUALS                │  │
    ├─────────────────────────────┤  │
    │ PK document_id              │←─┘
    │    model_numbers (Array)    │
    │    brand                    │
    │    appliance_category       │
    │    manual_type              │
    │    language                 │
    │    version                  │
    │    year                     │
    │    file_name                │
    │    file_hash (UNIQUE)       │
    │    content_hash             │
    │    file_size                │
    │    page_count               │
    │    gcs_uri                  │
    │    source_url               │
    │    download_url             │
    │    processor                │
    │    indexed                  │
    │    metadata (JSONB)         │
    └─────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────┐
│                    SERVICE & MAINTENANCE                             │
└──────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────┐
    │   SERVICE_EVENTS            │
    ├─────────────────────────────┤
    │ PK event_id                 │
    │ FK appliance_id             │
    │ FK user_id                  │
    │    event_type               │
    │    event_date               │
    │    description              │
    │    technician               │
    │    cost                     │
    │    warranty_covered         │
    │    parts_replaced (JSONB)   │
    │    notes                    │
    └─────────────────────────────┘

    ┌─────────────────────────────┐
    │  MAINTENANCE_SCHEDULES      │
    ├─────────────────────────────┤
    │ PK schedule_id              │
    │ FK appliance_id             │
    │    task_name                │
    │    frequency_months         │
    │    last_performed           │
    │    next_due                 │
    │    parts_needed (JSONB)     │
    │    estimated_cost           │
    │    reminder_enabled         │
    └─────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────┐
│                      TROUBLESHOOTING                                 │
└──────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────┐
    │ TROUBLESHOOTING_SESSIONS    │
    ├─────────────────────────────┤
    │ PK session_id               │
    │ FK user_id                  │
    │ FK appliance_id             │
    │    issue_summary            │
    │    symptoms (JSONB)         │
    │    error_codes (JSONB)      │
    │    conversation (JSONB)     │
    │    status                   │
    │    resolution               │
    │    resolved_at              │
    │    user_satisfaction        │
    └─────────────────────────────┘
            │
            │ 1:1 (optional)
            │
            ▼
    ┌─────────────────────────────┐
    │   SERVICE_TICKETS           │
    ├─────────────────────────────┤
    │ PK ticket_id                │
    │ FK user_id                  │
    │ FK appliance_id             │
    │ FK session_id               │
    │    status                   │
    │    priority                 │
    │    summary                  │
    │    symptoms (JSONB)         │
    │    error_codes (JSONB)      │
    │    assigned_to              │
    │    resolution               │
    └─────────────────────────────┘
```

---

## Table Specifications

### Core Indexes

```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- Homes
CREATE INDEX idx_homes_user ON homes(user_id);

-- Appliances (Critical for performance)
CREATE INDEX idx_appliances_user ON appliances(user_id);
CREATE INDEX idx_appliances_home ON appliances(home_id);
CREATE INDEX idx_appliances_category ON appliances(appliance_category);
CREATE INDEX idx_appliances_model ON appliances(model_number);
CREATE INDEX idx_appliances_brand_category ON appliances(brand, appliance_category);
CREATE INDEX idx_appliances_status ON appliances(status);

-- Manuals (Critical for deduplication)
CREATE UNIQUE INDEX idx_manuals_file_hash ON manuals(file_hash);
CREATE INDEX idx_manuals_content_hash ON manuals(content_hash);
CREATE INDEX idx_manuals_model ON manuals USING GIN(model_numbers);
CREATE INDEX idx_manuals_category ON manuals(appliance_category);
CREATE INDEX idx_manuals_brand_model ON manuals(brand, model_numbers);
CREATE INDEX idx_manuals_type ON manuals(manual_type);

-- Service Events
CREATE INDEX idx_service_appliance ON service_events(appliance_id);
CREATE INDEX idx_service_user ON service_events(user_id);
CREATE INDEX idx_service_date ON service_events(event_date DESC);
CREATE INDEX idx_service_type ON service_events(event_type);

-- Maintenance
CREATE INDEX idx_maint_appliance ON maintenance_schedules(appliance_id);
CREATE INDEX idx_maint_next_due ON maintenance_schedules(next_due);
CREATE INDEX idx_maint_overdue ON maintenance_schedules(next_due) WHERE next_due < CURRENT_DATE;

-- Troubleshooting
CREATE INDEX idx_ts_user ON troubleshooting_sessions(user_id);
CREATE INDEX idx_ts_appliance ON troubleshooting_sessions(appliance_id);
CREATE INDEX idx_ts_status ON troubleshooting_sessions(status);
CREATE INDEX idx_ts_created ON troubleshooting_sessions(created_at DESC);

-- Tickets
CREATE INDEX idx_tickets_user ON service_tickets(user_id);
CREATE INDEX idx_tickets_appliance ON service_tickets(appliance_id);
CREATE INDEX idx_tickets_status ON service_tickets(status);
CREATE INDEX idx_tickets_priority ON service_tickets(priority);
```

---

## Common Queries & Performance

### Query 1: Get user's appliances with manuals
```sql
SELECT
    a.*,
    COUNT(DISTINCT am.manual_id) as manual_count,
    array_agg(DISTINCT m.manual_type) as available_manual_types
FROM appliances a
LEFT JOIN appliance_manuals am ON a.instance_id = am.appliance_id
LEFT JOIN manuals m ON am.manual_id = m.document_id
WHERE a.user_id = $1
  AND a.status = 'active'
GROUP BY a.instance_id
ORDER BY a.created_at DESC;

-- Index used: idx_appliances_user, idx_appliances_status
-- Expected: <10ms for 20 appliances
```

### Query 2: Find manuals for specific appliance
```sql
SELECT m.*
FROM manuals m
JOIN appliance_manuals am ON m.document_id = am.manual_id
WHERE am.appliance_id = $1
ORDER BY
    CASE m.manual_type
        WHEN 'user' THEN 1
        WHEN 'troubleshooting' THEN 2
        WHEN 'installation' THEN 3
        WHEN 'service' THEN 4
        ELSE 5
    END;

-- Index used: appliance_manuals PK
-- Expected: <5ms
```

### Query 3: Check for duplicate manual (multi-level)
```sql
-- Level 1: File hash
SELECT document_id FROM manuals WHERE file_hash = $1;
-- Index: idx_manuals_file_hash (UNIQUE)
-- Expected: <1ms

-- Level 2: Content hash
SELECT document_id FROM manuals WHERE content_hash = $1;
-- Index: idx_manuals_content_hash
-- Expected: <2ms

-- Level 3: Composite key
SELECT document_id FROM manuals
WHERE brand = $1
  AND $2 = ANY(model_numbers)
  AND manual_type = $3
  AND version = $4;
-- Index: idx_manuals_brand_model, idx_manuals_type
-- Expected: <5ms
```

### Query 4: Get upcoming maintenance for user
```sql
SELECT
    a.nickname,
    a.location,
    ms.task_name,
    ms.next_due,
    ms.estimated_cost,
    EXTRACT(DAY FROM ms.next_due - CURRENT_DATE) as days_until_due
FROM maintenance_schedules ms
JOIN appliances a ON ms.appliance_id = a.instance_id
WHERE a.user_id = $1
  AND ms.next_due BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
  AND ms.reminder_enabled = true
ORDER BY ms.next_due ASC;

-- Index: idx_maint_next_due, idx_appliances_user
-- Expected: <10ms
```

### Query 5: Search troubleshooting history
```sql
SELECT
    ts.*,
    a.nickname as appliance_name,
    a.model_number
FROM troubleshooting_sessions ts
JOIN appliances a ON ts.appliance_id = a.instance_id
WHERE ts.user_id = $1
  AND ts.symptoms @> $2::jsonb  -- Search within JSONB array
ORDER BY ts.created_at DESC
LIMIT 10;

-- Index: idx_ts_user, idx_ts_created
-- JSONB GIN index for symptoms search (optional)
-- Expected: <20ms
```

---

## Data Growth Projections

### Storage Estimates (Per User)

**Average User (5 appliances)**
```
Appliances table:        5 rows × 1KB    = 5KB
Manuals (linked):        15 rows × 2KB   = 30KB  (3 manuals/appliance avg)
Service Events:          10 rows × 0.5KB = 5KB
Maintenance Schedules:   10 rows × 0.3KB = 3KB
Troubleshooting:         20 rows × 2KB   = 40KB
Tickets:                 5 rows × 1KB    = 5KB

Total per user: ~88KB
```

**At Scale (1M users)**
```
PostgreSQL: 1M × 88KB = 88GB
+ Indexes (~50%):        44GB
+ Growth buffer (20%):   26GB

Total: ~158GB PostgreSQL storage
```

**Qdrant Vectors**
```
Per manual: ~250 chunks × (1536 dims × 4 bytes + 2KB metadata) = ~2MB/manual

1M users × 5 appliances × 3 manuals/appliance = 15M manuals
15M manuals × 2MB = 30TB vectors

With deduplication (80% reuse):
30TB × 0.2 = 6TB actual unique vectors
```

---

## Backup & Recovery

### Backup Strategy

**PostgreSQL**
- Continuous WAL archiving (Point-in-Time Recovery)
- Daily full backups (retained 30 days)
- Weekly snapshots (retained 3 months)
- Cross-region replication

**Qdrant**
- Daily snapshots to GCS
- Incremental backups every 6 hours
- Retained 14 days

**GCS Files**
- Versioning enabled
- Lifecycle policy: Archive to Coldline after 90 days

### Recovery Procedures

**Scenario 1: Database corruption**
1. Stop application
2. Restore from last good backup
3. Replay WAL logs to point before corruption
4. Verify data integrity
5. Resume application

**Scenario 2: Accidental deletion**
1. Identify deletion timestamp
2. Point-in-Time Recovery to 1 minute before
3. Export deleted data
4. Re-import to current database

**Scenario 3: Complete disaster (region failure)**
1. Failover to secondary region
2. Promote read replica to primary
3. Update DNS/Load balancer
4. Verify data consistency

---

## Data Retention & Cleanup

### Retention Policies

```sql
-- Troubleshooting sessions: Keep 1 year
DELETE FROM troubleshooting_sessions
WHERE created_at < NOW() - INTERVAL '1 year'
  AND status = 'resolved';

-- Service tickets: Keep 3 years (compliance)
DELETE FROM service_tickets
WHERE created_at < NOW() - INTERVAL '3 years'
  AND status = 'closed';

-- Old appliances: Archive after 2 years of inactivity
UPDATE appliances
SET status = 'archived'
WHERE status = 'active'
  AND instance_id NOT IN (
      SELECT DISTINCT appliance_id
      FROM service_events
      WHERE event_date > NOW() - INTERVAL '2 years'
  );
```

### Manual Cleanup Jobs

Run monthly:
```sql
-- Remove orphaned manual links
DELETE FROM appliance_manuals
WHERE appliance_id NOT IN (SELECT instance_id FROM appliances);

-- Clean up old sessions in Redis
redis-cli --scan --pattern "session:*" | \
  xargs -L 1 redis-cli DEL

-- Vacuum & analyze
VACUUM ANALYZE appliances;
VACUUM ANALYZE manuals;
VACUUM ANALYZE troubleshooting_sessions;
```

---

## Security Considerations

### Row-Level Security (RLS)

```sql
-- Enable RLS on sensitive tables
ALTER TABLE appliances ENABLE ROW LEVEL SECURITY;
ALTER TABLE troubleshooting_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_tickets ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own data
CREATE POLICY user_isolation_appliances ON appliances
    FOR ALL
    TO app_user
    USING (user_id = current_setting('app.user_id')::uuid);

CREATE POLICY user_isolation_sessions ON troubleshooting_sessions
    FOR ALL
    TO app_user
    USING (user_id = current_setting('app.user_id')::uuid);

-- Set user context in application
SET app.user_id = 'user_12345';
```

### Encryption

**At Rest**
- PostgreSQL: Transparent Data Encryption (TDE)
- GCS: Google-managed encryption keys
- Sensitive fields: Application-level encryption (AES-256)

**In Transit**
- TLS 1.3 for all connections
- Certificate pinning for mobile apps

### Sensitive Data

```sql
-- PII fields to encrypt
UPDATE appliances
SET serial_number = pgp_sym_encrypt(serial_number, 'encryption_key')
WHERE serial_number IS NOT NULL;

-- Decrypt on read
SELECT
    instance_id,
    pgp_sym_decrypt(serial_number::bytea, 'encryption_key') as serial_number
FROM appliances;
```

---

This database schema supports the full lifecycle of appliance ownership, from onboarding to troubleshooting to service, with strong performance, security, and scalability characteristics.
