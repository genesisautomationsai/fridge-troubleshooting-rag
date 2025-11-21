#!/usr/bin/env python3
"""
Generate Individual Accuracy Reports for Each Test Context

Creates a separate JSON accuracy report file for each test context.
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


def generate_accuracy_report(context_file: str) -> Dict[str, Any]:
    """
    Generate detailed accuracy report for a single context.

    Args:
        context_file: Path to context JSON file

    Returns:
        Detailed accuracy report
    """
    # Load context
    context = load_user_context(context_file)

    # Extract context fields
    brand = context['appliance']['brand']
    model = context['appliance']['model']
    appliance_type = context['appliance']['type']
    problem_desc = context['problem']['description']
    symptoms = context['problem']['symptoms']
    error_codes = context['problem'].get('error_codes', [])
    attempted_fixes = context['problem'].get('attempted_fixes', [])

    # Build query from problem description
    query = f"{appliance_type} {problem_desc}"

    # Run enhanced RAG search
    result = search_samsung_manuals_rag(
        query=query,
        top_k=5,
        user_model=model,
        user_brand=brand,
        appliance_type=appliance_type,
        min_similarity=0.7
    )

    # Extract accuracy score
    accuracy_score = result.get('accuracy_score', {})

    # Build detailed report
    report = {
        "test_metadata": {
            "context_file": Path(context_file).name,
            "test_date": None,  # Will be set when saved
            "user_id": context.get('user_id', 'unknown'),
            "session_id": context.get('session_id', 'unknown')
        },
        "appliance_info": {
            "brand": brand,
            "model": model,
            "type": appliance_type,
            "purchase_date": context['appliance'].get('purchase_date')
        },
        "problem_description": {
            "summary": problem_desc,
            "symptoms": symptoms,
            "error_codes": error_codes,
            "attempted_fixes": attempted_fixes,
            "query_generated": query
        },
        "search_results": {
            "total_results_found": result.get('num_results', 0),
            "found_relevant_information": result.get('found_information', False),
            "results_after_filtering": result.get('filtered_count', 0),
            "min_similarity_threshold": result.get('min_similarity_threshold', 0.7)
        },
        "accuracy_assessment": {
            "overall_accuracy_score": accuracy_score.get('accuracy', 0),
            "accuracy_level": accuracy_score.get('level', 'No Information'),
            "breakdown": {
                "problem_solution_relevance": {
                    "score": accuracy_score.get('breakdown', {}).get('similarity', 0),
                    "weight": "55%",
                    "description": "How well the retrieved content addresses the specific problem (MOST IMPORTANT)"
                },
                "model_match": {
                    "score": accuracy_score.get('breakdown', {}).get('model_match', 0),
                    "weight": "25%",
                    "description": "Whether we found the exact manual for this appliance model"
                },
                "brand_match": {
                    "score": accuracy_score.get('breakdown', {}).get('brand_match', 0),
                    "weight": "20%",
                    "description": "Whether the manual is from the correct brand"
                }
            },
            "error_details": {
                "has_error": accuracy_score.get('error') is not None,
                "error_type": accuracy_score.get('error'),
                "error_message": accuracy_score.get('error_message'),
                "detected_model_type": accuracy_score.get('detected_model_type'),
                "expected_type": accuracy_score.get('expected_type'),
                "user_model": accuracy_score.get('user_model')
            } if accuracy_score.get('error') else None,
            "interpretation": {
                "will_solve_problem": accuracy_score.get('accuracy', 0) >= 90,
                "confidence_message": _get_confidence_message(accuracy_score.get('accuracy', 0)),
                "recommendation": _get_recommendation(accuracy_score.get('accuracy', 0), result.get('num_results', 0))
            }
        },
        "top_results": []
    }

    # Add top results with full details
    if result.get('results'):
        for i, res in enumerate(result['results'][:3], 1):
            report['top_results'].append({
                "rank": i,
                "relevance_score": res.get('score', 0),
                "source_manual": {
                    "filename": res.get('metadata', {}).get('source', 'Unknown'),
                    "brand": res.get('metadata', {}).get('brand', 'Unknown'),
                    "model": res.get('metadata', {}).get('model_number', 'Unknown'),
                    "appliance_type": res.get('metadata', {}).get('appliance_type', 'Unknown')
                },
                "content_preview": res.get('text', '')[:300],
                "full_content": res.get('text', '')
            })

    return report


def _get_confidence_message(accuracy: float) -> str:
    """Get human-readable confidence message."""
    if accuracy >= 90:
        return "Very High - The troubleshooting steps will very likely solve this specific problem for this appliance model."
    elif accuracy >= 75:
        return "High - The troubleshooting steps should effectively address this problem."
    elif accuracy >= 60:
        return "Medium - The steps might help but may not fully resolve the issue."
    elif accuracy >= 40:
        return "Low - The steps may not directly address this specific problem."
    else:
        return "Very Low - No relevant information found or steps unlikely to solve this problem."


def _get_recommendation(accuracy: float, num_results: int) -> str:
    """Get recommendation based on accuracy."""
    if accuracy >= 90:
        return "Proceed with the recommended troubleshooting steps. High probability of resolving the issue."
    elif accuracy >= 75:
        return "Follow the troubleshooting steps. Good chance of resolving the issue."
    elif accuracy >= 60:
        return "Try the suggested steps, but may need additional assistance."
    elif num_results == 0:
        return "No relevant manual information found. Consider contacting professional service or checking if the correct manual is available."
    else:
        return "Low confidence in current results. May need professional service or additional troubleshooting resources."


def main():
    """Generate individual accuracy reports for all contexts."""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Generate individual accuracy reports")
    parser.add_argument(
        "--contexts-dir",
        default="test_contexts",
        help="Directory containing context files"
    )
    parser.add_argument(
        "--output-dir",
        default="accuracy_reports",
        help="Output directory for accuracy reports"
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Find all context files
    contexts_path = Path(args.contexts_dir)
    context_files = sorted(contexts_path.glob("user_context_*.json"))

    print("=" * 60)
    print("GENERATING INDIVIDUAL ACCURACY REPORTS")
    print("=" * 60)
    print(f"Found {len(context_files)} test contexts")
    print(f"Output directory: {output_dir}")
    print()

    results_summary = []

    for i, context_file in enumerate(context_files, 1):
        context_name = context_file.stem
        output_file = output_dir / f"{context_name}_accuracy.json"

        print(f"[{i}/{len(context_files)}] Processing: {context_file.name}...", end=" ")

        try:
            # Generate report
            report = generate_accuracy_report(str(context_file))

            # Add test date
            report['test_metadata']['test_date'] = datetime.now().isoformat()

            # Save to JSON file
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)

            accuracy = report['accuracy_assessment']['overall_accuracy_score']
            level = report['accuracy_assessment']['accuracy_level']

            print(f"✓ {accuracy}% ({level})")
            print(f"   → Saved to: {output_file.name}")

            results_summary.append({
                "file": context_file.name,
                "output": output_file.name,
                "accuracy": accuracy,
                "level": level
            })

        except Exception as e:
            print(f"✗ Error: {e}")

    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total reports generated: {len(results_summary)}")
    print()

    # Sort by accuracy
    results_summary.sort(key=lambda x: x['accuracy'], reverse=True)

    print("Accuracy Rankings:")
    for i, result in enumerate(results_summary, 1):
        print(f"{i}. {result['file']}")
        print(f"   Accuracy: {result['accuracy']}% ({result['level']})")
        print(f"   Report: {result['output']}")
        print()

    print(f"✓ All reports saved to: {output_dir}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
