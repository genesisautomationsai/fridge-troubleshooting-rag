"""
Shared Tools for Samsung Refrigerator Troubleshooting Agents (RAG Version)
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RAG pipeline import
from rag_pipeline.retriever import search_manuals_rag

# Configuration
SAFETY_POLICY_PATH = os.getenv("SAFETY_POLICY_PATH", "./config/policy_safety.yaml")

# Load safety policy
try:
    with open(SAFETY_POLICY_PATH, "r") as f:
        SAFETY_POLICY = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Warning: Safety policy file not found at {SAFETY_POLICY_PATH}")
    SAFETY_POLICY = {"blocked_actions": [], "required_warnings": []}


def search_samsung_manuals_rag(query: str, top_k: int = 5) -> dict:
    """
    Search Samsung refrigerator manuals using RAG system.

    This uses the custom RAG pipeline:
    1. Embeds the query using OpenAI
    2. Searches Qdrant vector store for relevant chunks
    3. Returns context with similarity scores

    Args:
        query: Search query describing the problem or topic
        top_k: Number of results to return

    Returns:
        Dictionary with search results and context
    """
    return search_manuals_rag(
        query=query,
        top_k=top_k,
        brand=None,
        product_type=None
    )


def check_safety(plan_description: str) -> dict:
    """
    Check if a troubleshooting plan contains any unsafe actions.

    Args:
        plan_description: Description of the troubleshooting steps

    Returns:
        Dictionary with safety status, warnings, and blocked actions
    """
    warnings = []
    blocked_actions = []

    plan_lower = plan_description.lower()

    # Check for blocked actions
    for blocked in SAFETY_POLICY.get("blocked_actions", []):
        keywords = blocked.get("keywords", [])
        if any(keyword.lower() in plan_lower for keyword in keywords):
            blocked_actions.append({
                "reason": blocked.get("message"),
                "severity": blocked.get("severity", "HIGH")
            })

    # Check for required warnings
    for warning_rule in SAFETY_POLICY.get("required_warnings", []):
        condition = warning_rule.get("condition", {})
        keywords = condition.get("keywords", [])
        if any(keyword.lower() in plan_lower for keyword in keywords):
            warnings.append({
                "message": warning_rule.get("warning"),
                "severity": warning_rule.get("severity", "MEDIUM")
            })

    # General safety warnings
    if any(word in plan_lower for word in ["unplug", "power", "electrical"]):
        warnings.append({
            "message": "⚠️ ALWAYS unplug the refrigerator before performing any maintenance.",
            "severity": "HIGH"
        })

    safety_ok = len(blocked_actions) == 0

    return {
        "safety_ok": safety_ok,
        "warnings": warnings,
        "blocked_actions": blocked_actions,
        "recommendation": "Proceed with caution" if safety_ok else "Professional service required"
    }


def create_service_ticket(
    issues: List[Dict[str, Any]],
    model: Optional[str] = None
) -> dict:
    """
    Create a consolidated service ticket for unresolved refrigerator issues.

    Args:
        issues: List of issue dictionaries
        model: Refrigerator model number

    Returns:
        Dictionary with ticket ID and details
    """
    ticket_id = f"TCK-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"

    # Collect all symptoms, error codes, and attempted steps
    all_symptoms = []
    all_error_codes = []
    all_attempted_steps = []

    for issue in issues:
        all_symptoms.extend(issue.get("symptoms", []))
        all_error_codes.extend(issue.get("error_codes", []))
        all_attempted_steps.extend(issue.get("attempted_steps", []))

    # Create summary
    issue_summaries = [issue.get("summary", "Unknown issue") for issue in issues]
    combined_summary = f"Multiple issues reported: {'; '.join(issue_summaries)}"

    ticket = {
        "ticket_id": ticket_id,
        "status": "OPEN",
        "created_at": datetime.now().isoformat(),
        "number_of_issues": len(issues),
        "combined_summary": combined_summary,
        "model": model or "Unknown",
        "issues": issues,
        "all_symptoms": list(set(all_symptoms)),
        "all_error_codes": list(set(all_error_codes)),
        "all_attempted_steps": list(set(all_attempted_steps)),
        "priority": "high" if all_error_codes else "medium"
    }

    # Save ticket
    ticket_file = f"tickets/{ticket_id}.json"
    os.makedirs("tickets", exist_ok=True)

    try:
        with open(ticket_file, "w") as f:
            json.dump(ticket, f, indent=2)
        saved_message = f" Ticket saved to {ticket_file}"
    except Exception as e:
        saved_message = f" (Note: Could not save to file: {e})"

    return {
        "success": True,
        "ticket_id": ticket_id,
        "message": f"Service ticket {ticket_id} created successfully with {len(issues)} issue(s).{saved_message}",
        "ticket_details": ticket
    }


def get_current_time() -> dict:
    """
    Get the current date and time.

    Returns:
        Dictionary with current datetime
    """
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "datetime": now.isoformat()
    }
