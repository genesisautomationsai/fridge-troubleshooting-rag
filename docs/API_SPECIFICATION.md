# API Specification

## Base URL
```
Production:  https://api.homeappliance.ai/v1
Staging:     https://staging-api.homeappliance.ai/v1
Development: http://localhost:8000/v1
```

## Authentication

All API requests require authentication via JWT tokens.

### Headers
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Token Management

**POST /auth/login**
```json
Request:
{
    "email": "user@example.com",
    "password": "secure_password"
}

Response:
{
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 3600,
    "token_type": "Bearer",
    "user": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "name": "John Doe"
    }
}
```

**POST /auth/refresh**
```json
Request:
{
    "refresh_token": "eyJhbGc..."
}

Response:
{
    "access_token": "eyJhbGc...",
    "expires_in": 3600
}
```

---

## Appliance Onboarding

### POST /appliances/onboard

Onboard multiple appliances at once. System will auto-discover and download manuals.

```json
Request:
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "home_id": "660e8400-e29b-41d4-a716-446655440001",
    "appliances": [
        {
            "brand": "Samsung",
            "model_number": "RF28HMEDBSR",
            "appliance_category": "refrigerator",
            "nickname": "Kitchen Fridge",
            "location": "Kitchen",
            "purchase_date": "2024-06-15",
            "purchase_price": 2499.99,
            "retailer": "Home Depot",
            "serial_number": "012345ABC6789",
            "warranty_end": "2025-06-15"
        },
        {
            "brand": "LG",
            "model_number": "WM9000HVA",
            "appliance_category": "washer",
            "nickname": "Main Washer",
            "location": "Laundry Room",
            "purchase_date": "2024-03-10"
        }
    ]
}

Response: 202 Accepted
{
    "job_id": "job_abc123",
    "status": "processing",
    "message": "Onboarding 2 appliances. Manual discovery in progress.",
    "appliances_created": [
        {
            "instance_id": "appliance_xyz789",
            "brand": "Samsung",
            "model": "RF28HMEDBSR",
            "status": "pending_manuals"
        },
        {
            "instance_id": "appliance_def456",
            "brand": "LG",
            "model": "WM9000HVA",
            "status": "pending_manuals"
        }
    ],
    "check_status_url": "/jobs/job_abc123"
}
```

### GET /jobs/{job_id}

Check onboarding job status.

```json
Response:
{
    "job_id": "job_abc123",
    "status": "completed",  // processing | completed | failed
    "progress": {
        "total_appliances": 2,
        "completed": 2,
        "failed": 0
    },
    "results": [
        {
            "instance_id": "appliance_xyz789",
            "brand": "Samsung",
            "model": "RF28HMEDBSR",
            "manuals_found": 3,
            "manual_types": ["user", "installation", "service"],
            "indexed": true,
            "recalls_found": 0
        },
        {
            "instance_id": "appliance_def456",
            "brand": "LG",
            "model": "WM9000HVA",
            "manuals_found": 2,
            "manual_types": ["user", "installation"],
            "indexed": true,
            "recalls_found": 1
        }
    ],
    "completed_at": "2025-11-20T14:30:00Z"
}
```

---

## Appliance Management

### GET /users/{user_id}/appliances

Get all appliances for a user.

```json
Response:
{
    "appliances": [
        {
            "instance_id": "appliance_xyz789",
            "brand": "Samsung",
            "appliance_category": "refrigerator",
            "appliance_subcategory": "french_door",
            "model_number": "RF28HMEDBSR",
            "model_name": "Family Hub French Door",
            "nickname": "Kitchen Fridge",
            "location": "Kitchen",
            "purchase_date": "2024-06-15",
            "age_months": 5,
            "warranty_status": "active",
            "warranty_expires": "2025-06-15",
            "status": "active",
            "manuals_count": 3,
            "last_service": "2024-12-01",
            "next_maintenance": "2025-03-15"
        }
    ],
    "total": 5,
    "home_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### GET /appliances/{instance_id}

Get detailed appliance information.

```json
Response:
{
    "instance_id": "appliance_xyz789",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "home_id": "660e8400-e29b-41d4-a716-446655440001",

    "product_info": {
        "brand": "Samsung",
        "appliance_category": "refrigerator",
        "appliance_subcategory": "french_door",
        "model_number": "RF28HMEDBSR",
        "model_name": "Family Hub French Door",
        "serial_number": "012345ABC6789",
        "sku": "RF28HMEDBSR/AA",
        "features": ["ice_maker", "water_dispenser", "wifi_enabled", "smart_hub"],
        "specifications": {
            "capacity": "28 cu. ft.",
            "voltage": "115V",
            "dimensions": {"width": 35.75, "height": 70, "depth": 36.5, "unit": "inches"},
            "energy_rating": "Energy Star"
        }
    },

    "ownership": {
        "nickname": "Kitchen Fridge",
        "location": "Kitchen",
        "purchase_date": "2024-06-15",
        "purchase_price": 2499.99,
        "retailer": "Home Depot",
        "age_months": 5
    },

    "warranty": {
        "status": "active",
        "type": "manufacturer",
        "start_date": "2024-06-15",
        "end_date": "2025-06-15",
        "days_remaining": 207,
        "provider": "Samsung"
    },

    "manuals": [
        {
            "document_id": "doc_abc123",
            "manual_type": "user",
            "language": "en",
            "version": "2.0",
            "page_count": 936,
            "download_url": "/manuals/doc_abc123/download"
        },
        {
            "document_id": "doc_def456",
            "manual_type": "installation",
            "language": "en",
            "page_count": 24
        }
    ],

    "service_history": [
        {
            "event_id": "service_001",
            "date": "2024-12-01",
            "type": "repair",
            "description": "Ice maker replaced",
            "cost": 0.00,
            "warranty_covered": true
        }
    ],

    "maintenance": [
        {
            "task": "Replace water filter",
            "next_due": "2025-03-15",
            "days_until_due": 114,
            "part_number": "HAF-CIN",
            "estimated_cost": 45.00
        }
    ],

    "recalls": [],

    "created_at": "2024-06-20T10:00:00Z",
    "updated_at": "2024-12-01T14:30:00Z"
}
```

### PUT /appliances/{instance_id}

Update appliance information.

```json
Request:
{
    "nickname": "Main Fridge",
    "location": "Kitchen - North Wall",
    "notes": "Replaced ice maker under warranty"
}

Response: 200 OK
{
    "instance_id": "appliance_xyz789",
    "nickname": "Main Fridge",
    "location": "Kitchen - North Wall",
    "updated_at": "2025-11-20T15:00:00Z"
}
```

---

## Search & Troubleshooting

### POST /search

Search user's appliance manuals.

```json
Request:
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "query": "ice maker not working",
    "appliance_id": "appliance_xyz789",  // Optional: filter to specific appliance
    "filters": {
        "manual_type": "user",  // Optional
        "appliance_category": "refrigerator"  // Optional
    },
    "top_k": 5
}

Response:
{
    "query": "ice maker not working",
    "results": [
        {
            "chunk_id": "chunk_1234",
            "score": 0.89,
            "text": "Ice Maker Troubleshooting\n\nIf the ice maker is not producing ice:\n1. Check that the ice maker is turned ON...",
            "page_number": 42,
            "section": "Troubleshooting - Ice Maker",
            "appliance": {
                "instance_id": "appliance_xyz789",
                "nickname": "Kitchen Fridge",
                "model": "RF28HMEDBSR"
            },
            "manual": {
                "document_id": "doc_abc123",
                "manual_type": "user",
                "page_count": 936
            }
        },
        {
            "chunk_id": "chunk_5678",
            "score": 0.85,
            "text": "Ice Production Issues\n\nLow ice production can be caused by:\n- Water filter clogged...",
            "page_number": 44,
            "section": "Troubleshooting - Ice Maker"
        }
    ],
    "total_results": 5,
    "search_time_ms": 45
}
```

### POST /troubleshooting/start

Start a troubleshooting session with AI assistant.

```json
Request:
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "appliance_id": "appliance_xyz789",  // Optional: auto-identified if not provided
    "issue": "My fridge is making a loud grinding noise and not cooling properly"
}

Response: 201 Created
{
    "session_id": "session_abc123",
    "status": "active",
    "appliance": {
        "instance_id": "appliance_xyz789",
        "nickname": "Kitchen Fridge",
        "model": "RF28HMEDBSR"
    },
    "initial_response": {
        "message": "I understand your Samsung Family Hub refrigerator is making a loud grinding noise and not cooling. Let me help troubleshoot this.\n\nFirst, I've identified a few possible causes:\n1. Evaporator fan motor issue\n2. Compressor problem\n3. Ice maker malfunction\n\nBefore we proceed, I need to ask:\n- Is the noise coming from the freezer or refrigerator section?\n- When did you first notice the cooling issue?",
        "extracted_symptoms": ["loud grinding noise", "not cooling"],
        "confidence": "high"
    },
    "created_at": "2025-11-20T15:00:00Z"
}
```

### POST /troubleshooting/{session_id}/message

Continue troubleshooting conversation.

```json
Request:
{
    "message": "The noise is from the freezer and I noticed it yesterday"
}

Response:
{
    "session_id": "session_abc123",
    "response": {
        "message": "Thank you. Based on the noise location and timing, this is likely an evaporator fan motor issue.\n\n**Troubleshooting Steps:**\n\n**Step 1: Check the ice buildup**\n- Open the freezer and look for excessive frost on the back wall\n- Expected: If you see heavy frost, proceed to Step 2\n\n**Step 2: Check the evaporator fan**\n- Listen closely to identify if the grinding comes from the back of the freezer\n- The fan may be hitting ice buildup\n\n**⚠️ SAFETY WARNING:**\nUnplug the refrigerator before performing any maintenance.\n\nShould I continue with the troubleshooting steps, or would you like me to create a service ticket?",

        "plan": [
            {"step": 1, "action": "Check for ice buildup", "expected": "Frost on back wall"},
            {"step": 2, "action": "Identify noise source", "expected": "Grinding from fan"},
            {"step": 3, "action": "Manual defrost (24 hours)", "expected": "Noise stops"},
            {"step": 4, "action": "If persists, replace fan motor", "requires_service": true}
        ],

        "retrieved_sources": [
            {
                "manual_type": "user",
                "section": "Troubleshooting - Unusual Noises",
                "page": 67
            }
        ],

        "safety_check": {
            "safe": true,
            "warnings": ["Unplug refrigerator before maintenance"],
            "blocked_actions": []
        }
    },
    "options": [
        {"id": "continue", "label": "Continue troubleshooting"},
        {"id": "create_ticket", "label": "Create service ticket"},
        {"id": "schedule_service", "label": "Schedule professional service"}
    ]
}
```

### POST /troubleshooting/{session_id}/complete

Mark session as resolved or escalate to service.

```json
Request:
{
    "status": "resolved",  // resolved | escalated | abandoned
    "resolution": "Manual defrost resolved the issue",
    "satisfaction": 5,  // 1-5
    "create_service_ticket": false
}

Response:
{
    "session_id": "session_abc123",
    "status": "resolved",
    "resolution": "Manual defrost resolved the issue",
    "duration_minutes": 15,
    "steps_completed": 3,
    "user_satisfaction": 5,
    "resolved_at": "2025-11-20T15:15:00Z"
}
```

---

## Service Tickets

### POST /tickets

Create a service ticket.

```json
Request:
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "appliance_id": "appliance_xyz789",
    "session_id": "session_abc123",  // Optional: link to troubleshooting
    "summary": "Evaporator fan motor replacement needed",
    "symptoms": ["loud grinding noise", "not cooling", "frost buildup"],
    "error_codes": [],
    "priority": "high",
    "preferred_service_date": "2025-11-25",
    "notes": "Under warranty until 2025-06-15"
}

Response: 201 Created
{
    "ticket_id": "TCK-2025-12345",
    "status": "open",
    "priority": "high",
    "appliance": {
        "model": "Samsung RF28HMEDBSR",
        "warranty_status": "active"
    },
    "estimated_cost": 0.00,  // Covered by warranty
    "next_steps": "A service technician will contact you within 24 hours to schedule an appointment.",
    "created_at": "2025-11-20T15:20:00Z"
}
```

### GET /users/{user_id}/tickets

Get user's service tickets.

```json
Response:
{
    "tickets": [
        {
            "ticket_id": "TCK-2025-12345",
            "status": "open",
            "priority": "high",
            "appliance": {
                "nickname": "Kitchen Fridge",
                "model": "RF28HMEDBSR"
            },
            "summary": "Evaporator fan motor replacement",
            "created_at": "2025-11-20T15:20:00Z",
            "estimated_resolution": "2025-11-25"
        }
    ],
    "total": 1,
    "filters": {
        "status": ["open", "in_progress"]
    }
}
```

---

## Maintenance

### GET /appliances/{instance_id}/maintenance

Get maintenance schedule for appliance.

```json
Response:
{
    "appliance_id": "appliance_xyz789",
    "schedules": [
        {
            "schedule_id": "maint_001",
            "task_name": "Replace water filter",
            "description": "Replace refrigerator water filter",
            "frequency_months": 6,
            "last_performed": "2024-09-15",
            "next_due": "2025-03-15",
            "days_until_due": 114,
            "status": "upcoming",  // overdue | due_soon | upcoming
            "parts_needed": [
                {
                    "part_name": "Water Filter",
                    "part_number": "HAF-CIN",
                    "purchase_url": "https://www.samsung.com/us/...",
                    "estimated_cost": 45.00
                }
            ],
            "diy": true,
            "instructions_url": "/manuals/doc_abc123?page=82"
        },
        {
            "schedule_id": "maint_002",
            "task_name": "Clean condenser coils",
            "frequency_months": 12,
            "next_due": "2025-06-15",
            "days_until_due": 206,
            "diy": true
        }
    ],
    "overdue_count": 0,
    "upcoming_30_days": 1
}
```

### POST /appliances/{instance_id}/maintenance

Create or update maintenance schedule.

```json
Request:
{
    "task_name": "Replace water filter",
    "frequency_months": 6,
    "last_performed": "2024-09-15",
    "reminder_enabled": true,
    "reminder_days_before": 7
}

Response: 201 Created
{
    "schedule_id": "maint_001",
    "next_due": "2025-03-15",
    "reminder_date": "2025-03-08"
}
```

### POST /maintenance/{schedule_id}/complete

Log completed maintenance.

```json
Request:
{
    "completed_date": "2025-03-15",
    "cost": 45.00,
    "notes": "Replaced HAF-CIN filter. Old filter was brown."
}

Response:
{
    "schedule_id": "maint_001",
    "completed_date": "2025-03-15",
    "next_due": "2025-09-15",  // Auto-calculated
    "service_event_id": "service_002"  // Logged in service history
}
```

---

## Recalls & Alerts

### GET /users/{user_id}/recalls

Check recalls for all user's appliances.

```json
Response:
{
    "recalls": [
        {
            "recall_id": "SAMSUNG-2024-ICE",
            "appliance_id": "appliance_xyz789",
            "appliance": {
                "nickname": "Kitchen Fridge",
                "model": "RF28HMEDBSR"
            },
            "severity": "moderate",
            "issue": "Ice maker may malfunction and cause freezer compartment to overheat",
            "date_issued": "2024-08-01",
            "affected_models": ["RF28HMEDBSR", "RF28HFEDBSR"],
            "action_required": "Contact Samsung for free repair",
            "status": "pending",  // pending | scheduled | completed
            "contact_url": "https://www.samsung.com/us/support/recall/...",
            "deadline": "2025-12-31"
        }
    ],
    "total": 1,
    "pending_action": 1
}
```

---

## Rate Limiting

```
Per User:
- 100 requests/minute
- 10,000 requests/day

Per IP:
- 1000 requests/minute

Troubleshooting Sessions:
- 10 new sessions/hour
- 100 messages/session

Onboarding:
- 50 appliances/day
```

**Response when rate limited:**
```json
HTTP 429 Too Many Requests
{
    "error": "rate_limit_exceeded",
    "message": "You have exceeded the rate limit of 100 requests per minute",
    "retry_after": 60,  // seconds
    "limit": 100,
    "remaining": 0,
    "reset_at": "2025-11-20T15:01:00Z"
}
```

---

## Error Responses

### Standard Error Format

```json
{
    "error": "resource_not_found",
    "message": "Appliance with ID 'appliance_xyz789' not found",
    "status_code": 404,
    "details": {
        "resource": "appliance",
        "id": "appliance_xyz789"
    },
    "request_id": "req_abc123",
    "timestamp": "2025-11-20T15:00:00Z"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `invalid_request` | 400 | Malformed request body |
| `authentication_required` | 401 | Missing or invalid auth token |
| `insufficient_permissions` | 403 | User lacks permission |
| `resource_not_found` | 404 | Resource doesn't exist |
| `duplicate_resource` | 409 | Resource already exists |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Server error |
| `service_unavailable` | 503 | Temporary outage |

---

## Webhooks (Optional Future Feature)

Subscribe to events:

```json
POST /webhooks
{
    "url": "https://your-app.com/webhooks/appliance",
    "events": [
        "maintenance.due",
        "recall.issued",
        "ticket.created",
        "ticket.resolved"
    ],
    "secret": "webhook_secret_123"
}

Webhook Payload:
{
    "event": "maintenance.due",
    "timestamp": "2025-11-20T15:00:00Z",
    "data": {
        "appliance_id": "appliance_xyz789",
        "task": "Replace water filter",
        "due_date": "2025-03-15"
    },
    "signature": "sha256=..."  // HMAC signature for verification
}
```

---

This API specification provides a complete interface for managing appliance lifecycles, troubleshooting, and maintenance in a multi-user, multi-appliance environment.
