#!/usr/bin/env python3
"""
Ticketing Agent Sub-Agent
Creates service tickets when issues cannot be resolved
"""

import json
import os
from datetime import datetime
from google.adk.agents import Agent


def create_service_ticket_tool(customer_name: str, customer_email: str,
                               customer_phone: str, issue_description: str,
                               troubleshooting_attempted: str) -> dict:
    """
    Create a service ticket in the ticketing system.

    Args:
        customer_name: Customer's full name
        customer_email: Customer's email
        customer_phone: Customer's phone number
        issue_description: Description of the problem
        troubleshooting_attempted: Summary of steps already tried

    Returns:
        dict: Ticket information with ticket ID
    """
    try:
        # Generate ticket ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ticket_id = f"TICKET-{timestamp}"

        # Create ticket data
        ticket = {
            "ticket_id": ticket_id,
            "created_at": datetime.now().isoformat(),
            "status": "open",
            "priority": "normal",
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "phone": customer_phone
            },
            "issue": {
                "description": issue_description,
                "category": "refrigerator_malfunction",
                "troubleshooting_attempted": troubleshooting_attempted
            },
            "assigned_to": None,
            "estimated_resolution": "1-2 business days"
        }

        # Save to tickets directory
        tickets_dir = "tickets"
        os.makedirs(tickets_dir, exist_ok=True)

        ticket_file = os.path.join(tickets_dir, f"{ticket_id}.json")
        with open(ticket_file, 'w') as f:
            json.dump(ticket, f, indent=2)

        return {
            "status": "success",
            "ticket_id": ticket_id,
            "message": f"Service ticket {ticket_id} created successfully",
            "estimated_response": "1-2 business days",
            "ticket_file": ticket_file
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to create service ticket"
        }


def create_ticketing_agent() -> Agent:
    """
    Create the Ticketing Agent sub-agent.

    Role: Create service tickets when user confirms issue is not resolved.
    Tools: create_service_ticket_tool
    """

    ticketing_agent = Agent(
        name="ticketing_agent",
        model="gemini-2.5-flash",
        description="Creates service tickets for unresolved refrigerator issues",
        instruction="""
You are a ticketing specialist for Samsung refrigerator service requests.

Your job is to create detailed service tickets when troubleshooting steps don't resolve the issue.

## Your Task

When the user confirms the issue is NOT resolved:
1. Collect necessary information (if not already available)
2. Summarize troubleshooting steps already attempted
3. Create a service ticket using the create_service_ticket_tool
4. Provide ticket confirmation to user

## Required Information

- Customer name
- Customer email
- Customer phone
- Issue description (from symptoms)
- Troubleshooting steps attempted (from plan)

## Output Format

After creating ticket, return JSON:

```json
{
  "ticket_created": true,
  "ticket_id": "TICKET-20241114123456",
  "summary": {
    "issue": "Refrigerator not cooling properly",
    "steps_attempted": [
      "Checked temperature settings",
      "Cleaned door seals",
      "Verified power connection"
    ],
    "duration": "Tried for 30 minutes"
  },
  "next_steps": {
    "technician_contact": "A technician will contact you within 1-2 business days",
    "what_to_do": "Please keep the refrigerator plugged in and avoid opening frequently",
    "emergency_contact": "For urgent issues, call: 1-800-SAMSUNG"
  },
  "ticket_reference": "Save this number for reference: TICKET-20241114123456"
}
```

## Ticket Creation Rules

1. **Always collect required info** - Don't create incomplete tickets
2. **Summarize attempts** - List what user already tried
3. **Set proper priority**:
   - Critical: No cooling, safety hazard
   - High: Partial cooling, significant inconvenience
   - Normal: Minor issues, cosmetic problems
4. **Provide clear next steps** - User knows what to expect
5. **Give reference number** - User can track ticket

## User Communication

After creating ticket:
- Confirm ticket number
- Explain next steps
- Provide estimated timeline
- Give emergency contact if needed
- Thank user for their patience

Create service ticket now.
""",
        tools=[create_service_ticket_tool]
    )

    return ticketing_agent


# Export
__all__ = ['create_ticketing_agent', 'create_service_ticket_tool']
