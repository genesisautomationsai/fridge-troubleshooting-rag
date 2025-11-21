#!/usr/bin/env python3
"""
Test All User Contexts and Output Accuracy Scores in JSON

Runs all test context files and generates a JSON report with accuracy scores.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from tools import search_samsung_manuals_rag, calculate_accuracy_score
from rag_pipeline.retriever import search_manuals_rag


def load_user_context(context_file: str) -> Dict[str, Any]:
    """Load user context from JSON file."""
    with open(context_file, 'r') as f:
        return json.load(f)


def test_single_context(context_file: str) -> Dict[str, Any]:
    """
    Test a single context and return accuracy results.

    Args:
        context_file: Path to context JSON file

    Returns:
        Dictionary with test results and accuracy score
    """
    # Load context
    context = load_user_context(context_file)

    # Extract context fields
    brand = context['appliance']['brand']
    model = context['appliance']['model']
    appliance_type = context['appliance']['type']
    problem_desc = context['problem']['description']

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

    # Build result dictionary
    test_result = {
        "context_file": Path(context_file).name,
        "appliance": {
            "brand": brand,
            "model": model,
            "type": appliance_type
        },
        "problem": problem_desc,
        "query": query,
        "results": {
            "num_results": result.get('num_results', 0),
            "found_information": result.get('found_information', False),
            "filtered_count": result.get('filtered_count', 0)
        },
        "accuracy": {
            "score": accuracy_score.get('accuracy', 0),
            "level": accuracy_score.get('level', 'No Information'),
            "breakdown": accuracy_score.get('breakdown', {
                "similarity": 0,
                "model_match": 0,
                "brand_match": 0
            })
        },
        "top_result": None
    }

    # Add top result if available
    if result.get('results'):
        top = result['results'][0]
        test_result['top_result'] = {
            "score": top.get('score', 0),
            "source": top.get('metadata', {}).get('source', 'Unknown'),
            "model": top.get('metadata', {}).get('model_number', 'Unknown'),
            "brand": top.get('metadata', {}).get('brand', 'Unknown'),
            "preview": top.get('text', '')[:200]
        }

    return test_result


def test_all_contexts(contexts_dir: str = "test_contexts") -> List[Dict[str, Any]]:
    """
    Test all context files in the directory.

    Args:
        contexts_dir: Directory containing context JSON files

    Returns:
        List of test results
    """
    contexts_path = Path(contexts_dir)
    context_files = sorted(contexts_path.glob("user_context_*.json"))

    results = []

    print(f"Found {len(context_files)} test contexts\n")

    for i, context_file in enumerate(context_files, 1):
        print(f"[{i}/{len(context_files)}] Testing: {context_file.name}...", end=" ")

        try:
            result = test_single_context(str(context_file))
            results.append(result)

            accuracy = result['accuracy']['score']
            level = result['accuracy']['level']
            print(f"✓ Accuracy: {accuracy}% ({level})")

        except Exception as e:
            print(f"✗ Error: {e}")
            results.append({
                "context_file": context_file.name,
                "error": str(e),
                "accuracy": {"score": 0, "level": "Error"}
            })

    return results


def generate_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary report from test results.

    Args:
        results: List of test results

    Returns:
        Summary report dictionary
    """
    total_tests = len(results)
    successful_tests = sum(1 for r in results if 'error' not in r)

    # Calculate statistics
    accuracy_scores = [r['accuracy']['score'] for r in results if 'error' not in r]

    if accuracy_scores:
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        max_accuracy = max(accuracy_scores)
        min_accuracy = min(accuracy_scores)
        high_accuracy = sum(1 for s in accuracy_scores if s >= 90)
        medium_accuracy = sum(1 for s in accuracy_scores if 75 <= s < 90)
        low_accuracy = sum(1 for s in accuracy_scores if s < 75)
    else:
        avg_accuracy = max_accuracy = min_accuracy = 0
        high_accuracy = medium_accuracy = low_accuracy = 0

    return {
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "average_accuracy": round(avg_accuracy, 1),
            "max_accuracy": round(max_accuracy, 1),
            "min_accuracy": round(min_accuracy, 1),
            "high_accuracy_count": high_accuracy,  # >= 90%
            "medium_accuracy_count": medium_accuracy,  # 75-89%
            "low_accuracy_count": low_accuracy  # < 75%
        },
        "results": results
    }


def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Test all user contexts and output accuracy scores")
    parser.add_argument(
        "--output",
        default="accuracy_report.json",
        help="Output JSON file path (default: accuracy_report.json)"
    )
    parser.add_argument(
        "--contexts-dir",
        default="test_contexts",
        help="Directory containing context files (default: test_contexts)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON output"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("TESTING ALL USER CONTEXTS")
    print("=" * 60)
    print()

    # Run all tests
    results = test_all_contexts(args.contexts_dir)

    # Generate report
    report = generate_report(results)

    # Save to JSON file
    with open(args.output, 'w') as f:
        if args.pretty:
            json.dump(report, f, indent=2)
        else:
            json.dump(report, f)

    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Successful: {report['summary']['successful_tests']}")
    print(f"Failed: {report['summary']['failed_tests']}")
    print()
    print(f"Average Accuracy: {report['summary']['average_accuracy']}%")
    print(f"Max Accuracy: {report['summary']['max_accuracy']}%")
    print(f"Min Accuracy: {report['summary']['min_accuracy']}%")
    print()
    print(f"High Accuracy (>=90%): {report['summary']['high_accuracy_count']} tests")
    print(f"Medium Accuracy (75-89%): {report['summary']['medium_accuracy_count']} tests")
    print(f"Low Accuracy (<75%): {report['summary']['low_accuracy_count']} tests")
    print()
    print(f"✓ Report saved to: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
