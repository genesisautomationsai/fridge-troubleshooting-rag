#!/usr/bin/env python3
"""
Test RAG System with User Context

Load user context from JSON file and test RAG search with confidence scoring.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
from tools import search_samsung_manuals_rag, calculate_accuracy_score
from rag_pipeline.retriever import search_manuals_rag


def load_user_context(context_file: str) -> Dict[str, Any]:
    """Load user context from JSON file."""
    with open(context_file, 'r') as f:
        return json.load(f)


def format_accuracy_display(accuracy: dict) -> str:
    """Format accuracy score for display."""
    score = accuracy['accuracy']
    level = accuracy['level']
    breakdown = accuracy['breakdown']

    output = f"\n{'='*60}\n"
    output += f"📊 ACCURACY SCORE: {score}% ({level})\n"
    output += f"{'='*60}\n"

    # Check for appliance type mismatch error
    if accuracy.get('error') == 'appliance_type_mismatch':
        output += f"\n⚠️  ERROR: WRONG APPLIANCE TYPE DETECTED\n"
        output += f"{'='*60}\n"
        output += f"{accuracy.get('error_message', 'Model mismatch detected')}\n"
        output += f"\nDetected: {accuracy.get('detected_model_type', 'Unknown')}\n"
        output += f"Expected: {accuracy.get('expected_type', 'Unknown')}\n"
        output += f"{'='*60}\n"
    else:
        output += f"  Manual Similarity:  {breakdown['similarity']}%\n"
        output += f"  Model Match:        {breakdown['model_match']}%\n"
        output += f"  Brand Match:        {breakdown['brand_match']}%\n"
        output += f"{'='*60}\n"

    return output


def test_rag_search(context: Dict[str, Any], query: str = None):
    """
    Test RAG search with user context.

    Args:
        context: User context dictionary
        query: Optional custom query (uses problem description if not provided)
    """
    # Extract context fields
    brand = context['appliance']['brand']
    model = context['appliance']['model']
    appliance_type = context['appliance']['type']

    # Use custom query or build from symptoms
    if query is None:
        problem_desc = context['problem']['description']
        query = f"{appliance_type} {problem_desc}"

    print("\n" + "="*60)
    print("RAG SEARCH TEST")
    print("="*60)
    print(f"User: {context['user_info']['name']}")
    print(f"Appliance: {brand} {appliance_type} - Model {model}")
    print(f"Problem: {context['problem']['description']}")
    print(f"Query: {query}")
    print("="*60)

    # Test 1: Basic RAG search (no confidence scoring)
    print("\n[TEST 1] Basic RAG Search (no filtering)")
    print("-" * 60)

    basic_result = search_manuals_rag(
        query=query,
        top_k=5,
        brand=brand,
        product_type=appliance_type
    )

    print(f"Status: {basic_result.get('status', 'unknown')}")
    print(f"Results found: {basic_result.get('num_results', 0)}")

    if basic_result.get('results'):
        print("\nTop Results:")
        for i, result in enumerate(basic_result['results'][:3], 1):
            score = result.get('score', 0)
            source = result.get('metadata', {}).get('source', 'Unknown')
            text_preview = result.get('text', '')[:150]
            print(f"  {i}. Score: {score:.3f} | Source: {source.split('/')[-1]}")
            print(f"     Preview: {text_preview}...")

    # Calculate accuracy for basic results
    accuracy_basic = calculate_accuracy_score(
        results=basic_result.get('results', []),
        user_model=model,
        user_brand=brand
    )

    print(format_accuracy_display(accuracy_basic))

    # Test 2: Enhanced RAG search with filtering (min_similarity=0.7)
    print("\n[TEST 2] Enhanced RAG Search (min_similarity=0.7)")
    print("-" * 60)

    enhanced_result = search_samsung_manuals_rag(
        query=query,
        top_k=5,
        user_model=model,
        user_brand=brand,
        appliance_type=appliance_type,
        min_similarity=0.7
    )

    print(f"Results found: {enhanced_result.get('num_results', 0)}")
    print(f"Filtered count: {enhanced_result.get('filtered_count', 0)}")
    print(f"Min similarity threshold: {enhanced_result.get('min_similarity_threshold', 0)}")

    if enhanced_result.get('results'):
        print("\nFiltered Results:")
        for i, result in enumerate(enhanced_result['results'][:3], 1):
            score = result.get('score', 0)
            source = result.get('metadata', {}).get('source', 'Unknown')
            result_model = result.get('metadata', {}).get('model_number', 'N/A')
            result_brand = result.get('metadata', {}).get('brand', 'N/A')
            text_preview = result.get('text', '')[:150]
            print(f"\n  {i}. Score: {score:.3f}")
            print(f"     Model: {result_model} | Brand: {result_brand}")
            print(f"     Source: {source.split('/')[-1]}")
            print(f"     Preview: {text_preview}...")

    # Display accuracy from enhanced search
    accuracy_enhanced = enhanced_result.get('accuracy_score', {})
    print(format_accuracy_display(accuracy_enhanced))

    # Test 3: Try different similarity thresholds
    print("\n[TEST 3] Testing Different Similarity Thresholds")
    print("-" * 60)

    for threshold in [0.9, 0.8, 0.7, 0.6, 0.5]:
        result = search_samsung_manuals_rag(
            query=query,
            top_k=5,
            user_model=model,
            user_brand=brand,
            appliance_type=appliance_type,
            min_similarity=threshold
        )

        num_results = result.get('num_results', 0)
        accuracy = result.get('accuracy_score', {}).get('accuracy', 0)
        level = result.get('accuracy_score', {}).get('level', 'N/A')

        print(f"  Threshold {threshold}: {num_results} results | Accuracy: {accuracy}% ({level})")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Basic search accuracy: {accuracy_basic['accuracy']}% ({accuracy_basic['level']})")
    print(f"✅ Enhanced search accuracy: {accuracy_enhanced['accuracy']}% ({accuracy_enhanced['level']})")

    if accuracy_enhanced['accuracy'] >= 90:
        print("\n🎯 SUCCESS: Accuracy score is 90% or higher!")
        print("   The troubleshooting steps will accurately solve the problem for this model.")
    elif accuracy_enhanced['accuracy'] >= 75:
        print("\n⚠️  GOOD: Accuracy score is 75%+, but not quite 90%")
        print("   The troubleshooting steps should work for this model.")
    else:
        print("\n❌ LOW: Accuracy score is below 75%")
        print("   Possible reasons:")
        print(f"   - Low similarity: {accuracy_enhanced['breakdown']['similarity']}%")
        print(f"   - Model mismatch: {accuracy_enhanced['breakdown']['model_match']}%")
        print(f"   - Brand mismatch: {accuracy_enhanced['breakdown']['brand_match']}%")

    print("="*60 + "\n")


def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Test RAG system with user context")
    parser.add_argument(
        "--context",
        required=True,
        help="Path to user context JSON file"
    )
    parser.add_argument(
        "--query",
        help="Custom search query (optional)"
    )

    args = parser.parse_args()

    # Load context
    print(f"\nLoading context from: {args.context}")
    context = load_user_context(args.context)

    # Run tests
    test_rag_search(context, query=args.query)


if __name__ == "__main__":
    main()
