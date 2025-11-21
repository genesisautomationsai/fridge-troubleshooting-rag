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


def _check_model_appliance_type(user_model: str, user_brand: Optional[str] = None) -> Optional[str]:
    """
    Check what appliance type a model number belongs to by searching the database.

    Args:
        user_model: User's model number
        user_brand: User's brand (optional, helps narrow search)

    Returns:
        Appliance type if found, None otherwise
    """
    try:
        from rag_pipeline.retriever import search_manuals_rag

        # Try multiple search strategies to find the model
        # Strategy 1: Search with just the model number (best for exact match)
        result = search_manuals_rag(
            query=user_model,
            top_k=10,  # Get more results to increase chances of finding the model
            brand=user_brand,
            product_type=None  # Don't filter by type, we want to find what type it is
        )

        # Check if we found the model with high confidence
        if result.get('results'):
            # Clean user model: remove *, **, and whitespace
            user_model_clean = user_model.upper().replace("**", "").replace("*", "").strip()

            # First pass: Look for exact or very close matches with wildcard handling
            for r in result['results']:
                result_model_raw = r.get('metadata', {}).get('model_number', '').upper()
                # Clean database model: remove *, **, and whitespace
                result_model_clean = result_model_raw.replace("**", "").replace("*", "").strip()
                result_score = r.get('score', 0)

                # Exact match after removing wildcards
                if user_model_clean == result_model_clean:
                    return r.get('metadata', {}).get('appliance_type', '').lower()

                # Check if they share a common prefix (for wildcard matches)
                # E.g., WD53DBA900H and WD53DBA9H both start with WD53DBA9
                if result_score > 0.5 and len(result_model_clean) >= 6:
                    # Use the length of the shorter model as the prefix length
                    min_len = min(len(user_model_clean), len(result_model_clean))
                    # Check if they match for at least the shorter model's length
                    if min_len >= 6:
                        user_prefix = user_model_clean[:min_len]
                        db_prefix = result_model_clean[:min_len]
                        if user_prefix == db_prefix:
                            return r.get('metadata', {}).get('appliance_type', '').lower()

            # Second pass: Look for partial matches with high scores
            for r in result['results']:
                result_model_raw = r.get('metadata', {}).get('model_number', '').upper()
                result_model_clean = result_model_raw.replace("**", "").replace("*", "").strip()
                result_score = r.get('score', 0)

                # If high similarity score and significant model number overlap
                if result_score > 0.4 and len(result_model_clean) >= 6:
                    # Check if they share at least 80% of characters in common prefix
                    min_len = min(len(user_model_clean), len(result_model_clean))
                    if min_len >= 6:
                        # Count matching prefix characters
                        matching_chars = 0
                        for i in range(min_len):
                            if user_model_clean[i] == result_model_clean[i]:
                                matching_chars += 1
                            else:
                                break  # Stop at first mismatch

                        # If at least 80% of the shorter model matches
                        if matching_chars >= min_len * 0.8:
                            return r.get('metadata', {}).get('appliance_type', '').lower()

        return None
    except Exception as e:
        # Silent failure - if we can't check, we won't block the search
        return None


def calculate_accuracy_score(results: list, user_model: Optional[str] = None, user_brand: Optional[str] = None,
                            user_appliance_type: Optional[str] = None) -> dict:
    """
    Calculate accuracy score for troubleshooting information.

    This score represents how accurately the troubleshooting steps will solve
    the problem for the user's specific appliance model.

    Args:
        results: List of RAG search results with scores and metadata
        user_model: User's appliance model number
        user_brand: User's appliance brand
        user_appliance_type: User's appliance type (refrigerator, microwave, etc.)

    Returns:
        Dictionary with accuracy score and breakdown
    """
    if not results:
        return {
            "accuracy": 0,
            "level": "No Information",
            "breakdown": {"similarity": 0, "model_match": 0, "brand_match": 0}
        }

    # Check for appliance type mismatch (wrong model provided)
    if user_model and user_appliance_type:
        user_type_lower = user_appliance_type.lower()

        # Check what appliance type the user's model actually belongs to
        actual_type = _check_model_appliance_type(user_model, user_brand)

        if actual_type and actual_type != user_type_lower:
            # Wrong appliance type - model exists but for different appliance!
            return {
                "accuracy": 0,
                "level": "Wrong Appliance Type",
                "breakdown": {"similarity": 0, "model_match": 0, "brand_match": 0},
                "error": "appliance_type_mismatch",
                "error_message": f"⚠️ ERROR: The model {user_model} is a {actual_type}, not a {user_type_lower}. Please provide the correct {user_type_lower} model number.",
                "detected_model_type": actual_type,
                "expected_type": user_type_lower,
                "user_model": user_model
            }

    # Get average similarity score (0-100) - only from top 3 results for better accuracy
    top_results = results[:min(3, len(results))]
    avg_similarity = (sum(r.get("score", 0) for r in top_results) / len(top_results)) * 100

    # Check model match - look for exact or series match
    model_match = 0
    if user_model:
        user_model_clean = user_model.upper().replace("*", "").strip()
        # Extract model series (first part before numbers/letters)
        user_series = ''.join(c for c in user_model_clean[:8] if c.isalnum())

        for result in results:
            result_model = result.get("metadata", {}).get("model_number", "").upper()
            if result_model:
                # Exact match or contains
                if user_model_clean in result_model or result_model in user_model_clean:
                    model_match = 100
                    break
                # Series match (e.g., RS28A5F vs RS28A5F61)
                elif user_series and user_series in result_model:
                    model_match = 80
                    break
                # Same brand series
                elif any(part in result_model for part in user_model_clean.split() if len(part) > 3):
                    model_match = 50

    # Check brand match - more flexible matching
    brand_match = 0
    if user_brand:
        user_brand_upper = user_brand.upper()
        for result in results:
            result_brand = result.get("metadata", {}).get("brand", "").upper()
            if result_brand:
                # Exact brand match
                if user_brand_upper in result_brand or result_brand in user_brand_upper:
                    brand_match = 100
                    break
                # Partial match (e.g., "SAMSUNG" in "SAMSUNG ELECTRONICS")
                elif any(word in result_brand for word in user_brand_upper.split()):
                    brand_match = 100
                    break

    # If no explicit brand provided, try to infer from model
    if brand_match == 0 and not user_brand and user_model:
        # Common brand prefixes in model numbers
        model_upper = user_model.upper()
        for result in results:
            result_brand = result.get("metadata", {}).get("brand", "").upper()
            if result_brand:
                # Check if model matches brand naming
                if "SAMSUNG" in result_brand and ("RS" in model_upper or "RF" in model_upper or "MC" in model_upper):
                    brand_match = 80
                    break
                elif "LG" in result_brand and ("LRM" in model_upper or "LFX" in model_upper):
                    brand_match = 80
                    break
                elif "GE" in result_brand and ("GNE" in model_upper or "GTE" in model_upper):
                    brand_match = 80
                    break

    # Weighted accuracy score (prioritizing problem-solving effectiveness)
    # Similarity is weighted most heavily because it measures how well the content
    # actually addresses the customer's specific problem
    accuracy = (
        avg_similarity * 0.55 +    # 55% from problem-solution relevance (most important)
        model_match * 0.25 +       # 25% from model match
        brand_match * 0.20         # 20% from brand match
    )

    # Determine accuracy level
    if accuracy >= 90:
        level = "Very High"
    elif accuracy >= 75:
        level = "High"
    elif accuracy >= 60:
        level = "Medium"
    elif accuracy >= 40:
        level = "Low"
    else:
        level = "Very Low"

    return {
        "accuracy": round(accuracy, 1),
        "level": level,
        "breakdown": {
            "similarity": round(avg_similarity, 1),
            "model_match": model_match,
            "brand_match": brand_match
        }
    }


def search_samsung_manuals_rag(
    query: str,
    top_k: int = 5,
    user_model: Optional[str] = None,
    user_brand: Optional[str] = None,
    appliance_type: Optional[str] = None,
    min_similarity: float = 0.7
) -> dict:
    """
    Search appliance manuals using RAG system with confidence scoring and filtering.

    This uses the custom RAG pipeline:
    1. Embeds the query using OpenAI
    2. Searches Qdrant vector store for relevant chunks
    3. Filters by minimum similarity threshold (default 70%)
    4. Returns high-confidence results only
    5. Calculates confidence score for relevance to user's model

    Args:
        query: Search query describing the problem or topic
        top_k: Number of results to return (after filtering)
        user_model: User's appliance model number (for confidence scoring)
        user_brand: User's appliance brand (for confidence scoring)
        appliance_type: Appliance type filter (refrigerator, microwave, washer, etc.)
        min_similarity: Minimum similarity score threshold (0.0-1.0, default 0.7)

    Returns:
        Dictionary with search results, context, and confidence score
    """
    # Search with more results initially, then filter
    initial_top_k = top_k * 3  # Get 3x results for better filtering

    result = search_manuals_rag(
        query=query,
        top_k=initial_top_k,
        brand=user_brand,
        product_type=appliance_type
    )

    # Filter results by minimum similarity score
    all_results = result.get("results", [])
    filtered_results = [
        r for r in all_results
        if r.get("score", 0) >= min_similarity
    ]

    # If we have filtered results, use them; otherwise fall back to top results
    if filtered_results:
        # Take top_k from filtered results
        final_results = filtered_results[:top_k]
    else:
        # No results meet threshold - lower threshold slightly and retry
        fallback_threshold = max(0.5, min_similarity - 0.15)
        filtered_results = [
            r for r in all_results
            if r.get("score", 0) >= fallback_threshold
        ]
        final_results = filtered_results[:top_k] if filtered_results else all_results[:top_k]

    # Rebuild context with filtered results
    if final_results:
        context_parts = []
        for i, r in enumerate(final_results, 1):
            source = r.get("metadata", {}).get("source", "Unknown")
            text = r.get("text", "")
            score = r.get("score", 0)
            context_parts.append(f"[{i}] (Source: {source}, Relevance: {score:.2f})\n{text}\n")
        result["context"] = "\n".join(context_parts)

    # Update result with filtered data
    result["results"] = final_results
    result["num_results"] = len(final_results)
    result["found_information"] = len(final_results) > 0
    result["min_similarity_threshold"] = min_similarity
    result["filtered_count"] = len(filtered_results)

    # Calculate accuracy score
    accuracy = calculate_accuracy_score(
        results=final_results,
        user_model=user_model,
        user_brand=user_brand,
        user_appliance_type=appliance_type
    )

    # Add accuracy to result
    result["accuracy_score"] = accuracy

    return result


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
