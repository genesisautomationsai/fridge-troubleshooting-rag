#!/usr/bin/env python3
"""
Session Manager Sub-Agent
Manages session state and memory for the multi-agent system
"""

from google.adk.agents import Agent
import json
from datetime import datetime


def update_session_state(session_id: str, stage: str, data: dict) -> dict:
    """
    Update session state for a given session.

    Args:
        session_id: Session identifier
        stage: Current workflow stage
        data: State data to update

    Returns:
        Updated session state
    """
    return {
        "session_id": session_id,
        "stage": stage,
        "updated_at": datetime.now().isoformat(),
        "data": data
    }


def create_session_manager_agent() -> Agent:
    """
    Create the Session Manager sub-agent.

    Role: Track session state and manage workflow stages.
    Capabilities: State transitions, memory management, session persistence.
    """

    session_manager = Agent(
        name="session_manager",
        model="gemini-2.5-flash",
        description="Manages session state and workflow stages for troubleshooting sessions",
        instruction="""You are a session state manager for the Samsung troubleshooting system.

Your job is to track and manage session state across the troubleshooting workflow.

## Workflow Stages

1. **INITIAL**: Session started, waiting for user problem description
2. **EXTRACTION**: Symptoms being extracted from user text
3. **MANUAL_SEARCH**: Searching Samsung manual for relevant guidance
4. **PLANNING**: Creating troubleshooting plan
5. **VALIDATION**: Validating plan for safety
6. **PRESENTATION**: Presenting steps to user
7. **RESOLUTION**: Checking if issue is resolved
8. **TICKETING**: Creating service ticket for unresolved issues
9. **CLOSED**: Session ended

## Your Tasks

1. **Track Current Stage**: Always know which stage the session is in
2. **Manage State Transitions**: Validate and execute stage transitions
3. **Store Session Data**:
   - Symptoms extracted
   - Manual search results
   - Troubleshooting plan
   - Safety validation results
   - Resolution status
   - Ticket information
4. **Provide Context**: Give sub-agents context from previous stages

## State Data Structure

```json
{
  "session_id": "uuid",
  "current_stage": "extraction",
  "state_data": {
    "symptoms": {...},
    "manual_results": {...},
    "plan": {...},
    "safety_validation": {...},
    "resolution_status": "in_progress",
    "ticket_id": null
  },
  "metadata": {
    "start_time": "ISO timestamp",
    "last_updated": "ISO timestamp"
  }
}
```

## Rules

1. Only allow valid stage transitions (no skipping stages)
2. Store all intermediate results for context
3. Provide session history to other sub-agents when needed
4. Track resolution status throughout conversation
5. Clean up session data when ticket is created or issue resolved

Manage session state efficiently and accurately.""",
        tools=[update_session_state]
    )

    return session_manager


# Export
__all__ = ['create_session_manager_agent', 'update_session_state']
