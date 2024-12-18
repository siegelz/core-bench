#!/usr/bin/env python3

"""
Fix List Results Script

This script identifies and fixes results that were affected by a bug in the evaluation
script where list values were not being properly handled. Specifically, it:

1. Finds all result files in the benchmark/results directory
2. Identifies results containing list values
3. Re-evaluates these results with the fixed evaluation logic
4. Reports which results were affected (where correct list answers were previously marked wrong)

The bug specifically affected capsule-0921079 where list values like [0.1, 0.05, 0.01]
were being incorrectly evaluated, causing correct answers to be marked as incorrect.

The results have since been fixed in the paper, so this script should not be necessary
but is documented for historical purposes.

Usage: python3 benchmark_utils/fix_list_results.py
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark.evaluations import eval_result_file, eval_result_json
from typing import Dict, List, Tuple
import copy

def find_result_files(results_dir: str) -> List[str]:
    """Find all .json result files recursively in the given directory."""
    result_files = []
    for root, _, files in os.walk(results_dir):
        for file in files:
            if file.endswith('.json') and not file.endswith('.lock'):
                result_files.append(os.path.join(root, file))
    return result_files

def find_list_results(result_report: Dict, gt_result: List[Dict]) -> List[Tuple[str, bool]]:
    """Find list results and check if they match ground truth."""
    list_results = []
    for key in result_report.keys():
        if key in gt_result[0] and isinstance(gt_result[0][key], list):
            matches = result_report[key] == gt_result[0][key]
            list_results.append((key, matches))
    return list_results

def get_list_results(result_file: str, dataset_file: str) -> List[Tuple[str, List[Tuple[str, bool]], Dict]]:
    """Find results that contain list values and check if they match ground truth."""
    with open(result_file, "r") as f:
        results = json.load(f)
    with open(dataset_file, "r") as f:
        dataset = json.load(f)

    # Backwards compatibility
    if 'capsule_results' not in results:
        results = {"capsule_results": results}

    # List to store results with list values
    list_results = []
    modified = False

    for result in results['capsule_results']:
        # Find ground truth result
        gt_result = None
        for capsule in dataset:
            if capsule['capsule_id'] == result['capsule_id']:
                gt_result = capsule['results']
                break
        
        # Check for list values and evaluate
        if gt_result:
            list_matches = find_list_results(result['result_report'], gt_result)
            if list_matches:
                # Re-evaluate this result using imported eval_result_json
                evaluation = eval_result_json(gt_result, result['result_report'])
                result.update(evaluation)
                modified = True
                
                # Store the result details
                list_results.append((
                    result['capsule_id'], 
                    list_matches,
                    evaluation
                ))

    # Save changes if any results were modified
    if modified:
        with open(result_file, "w") as f:
            json.dump(results, f, indent=4)

    return list_results

def main():
    results_dir = "benchmark/results"
    dataset_file = "benchmark/dataset/core_test.json"
    
    print("Finding and re-evaluating result files...")
    result_files = find_result_files(results_dir)
    
    print(f"\nFound {len(result_files)} result files")
    print("\nResults containing list values (these were impacted by the fix):")
    print("------------------------------------------------------------")
    
    # Track statistics
    total_list_results = 0
    correct_list_results = 0
    affected_capsules = set()
    affected_files = []
    
    for result_file in result_files:
        try:
            list_results = get_list_results(result_file, dataset_file)
            
            if list_results:
                for capsule_id, matches, evaluation in list_results:
                    affected_capsules.add(capsule_id)
                    for key, is_correct in matches:
                        total_list_results += 1
                        if is_correct:
                            correct_list_results += 1
                            # Only print if this was a correct list result (affected by the bug)
                            if result_file not in affected_files:
                                affected_files.append(result_file)
                                print(f"\nFile: {result_file}")
                            print(f"\nCapsule: {capsule_id}")
                            print(f"  Key: {key}")
                            print(f"  Value matches ground truth - was previously marked incorrect due to list handling bug")
                            print("  Scores:")
                            print(f"    Written: {evaluation['correct_written_answers']}/{evaluation['total_written_questions']}")
                            print(f"    Vision: {evaluation['correct_vision_answers']}/{evaluation['total_vision_questions']}")
        except Exception as e:
            print(f"Error processing {result_file}: {str(e)}")
    
    print("\nSummary:")
    print("--------")
    print(f"Total files with list values: {len(affected_files)}")
    print(f"Total capsules with list values: {len(affected_capsules)}")
    print(f"Total list results: {total_list_results}")
    print(f"Correct list results: {correct_list_results}")

if __name__ == "__main__":
    main()
