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

def find_list_question_key(gt_result: List[Dict]) -> str:
    """Find the key in ground truth that expects a list value."""
    for key in gt_result[0].keys():
        if isinstance(gt_result[0][key], list):
            return key
    return None

def process_result_file(result_file: str, dataset_file: str) -> List[Tuple[str, Dict, Dict, bool]]:
    """Process a result file to fix list-related evaluations and total question counts."""
    with open(result_file, "r") as f:
        results = json.load(f)
    with open(dataset_file, "r") as f:
        dataset = json.load(f)

    # Backwards compatibility
    if 'capsule_results' not in results:
        results = {"capsule_results": results}

    fixed_results = []
    modified = False

    # Find the list question's key from ground truth
    list_key = None
    for capsule in dataset:
        if capsule['capsule_id'] == 'capsule-0921079':
            list_key = find_list_question_key(capsule['results'])
            break

    if not list_key:
        return fixed_results

    for result in results['capsule_results']:
        # Find ground truth result
        gt_result = None
        for capsule in dataset:
            if capsule['capsule_id'] == result['capsule_id']:
                gt_result = capsule['results']
                break
        
        if gt_result:
            # Store original scores
            original_scores = {
                'total_vision_questions': result.get('total_vision_questions', 0),
                'total_written_questions': result.get('total_written_questions', 0),
                'correct_vision_answers': result.get('correct_vision_answers', 0),
                'correct_written_answers': result.get('correct_written_answers', 0)
            }
            
            # Re-evaluate using evaluations.py logic
            evaluation = eval_result_json(gt_result, result['result_report'])
            
            # Check if this is the capsule with the list question
            if result['capsule_id'] == 'capsule-0921079':
                # Track if the answer was attempted and if it was correct
                attempted = list_key in result['result_report']
                is_correct = attempted and result['result_report'][list_key] == gt_result[0][list_key]
                
                # Update result with proper evaluation
                result.update(evaluation)
                modified = True
                
                # Store result details
                fixed_results.append((
                    result['capsule_id'],
                    original_scores,
                    evaluation,
                    is_correct,
                    attempted
                ))

    # Save changes if any results were modified
    if modified:
        with open(result_file, "w") as f:
            json.dump(results, f, indent=4)

    return fixed_results

def main():
    results_dir = "benchmark/results"
    dataset_file = "benchmark/dataset/core_test.json"
    
    print("Finding and re-evaluating result files...")
    result_files = find_result_files(results_dir)
    
    print(f"\nFound {len(result_files)} result files")
    print("\nResults affected by the list question fix:")
    print("----------------------------------------")
    
    # Track statistics
    total_attempts = 0
    correct_answers = 0
    fixed_totals = 0
    affected_files = []
    
    for result_file in result_files:
        try:
            fixed_results = process_result_file(result_file, dataset_file)
            
            if fixed_results:
                for capsule_id, old_scores, new_scores, is_correct, attempted in fixed_results:
                    if attempted:
                        total_attempts += 1
                    if is_correct:
                        correct_answers += 1
                    
                    # Check if totals were fixed
                    if old_scores['total_vision_questions'] != new_scores['total_vision_questions'] or \
                       old_scores['total_written_questions'] != new_scores['total_written_questions']:
                        fixed_totals += 1
                    
                    if result_file not in affected_files:
                        affected_files.append(result_file)
                        print(f"\nFile: {result_file}")
                    
                    print(f"\nCapsule: {capsule_id}")
                    if attempted:
                        if is_correct:
                            print("  Answer matches ground truth - was previously marked incorrect")
                        else:
                            print("  Answer attempted but incorrect")
                    else:
                        print("  No attempt at list question")
                    
                    if old_scores['total_vision_questions'] != new_scores['total_vision_questions']:
                        print(f"  Total vision questions fixed: {old_scores['total_vision_questions']} -> {new_scores['total_vision_questions']}")
                    print("  Scores after fix:")
                    print(f"    Written: {new_scores['correct_written_answers']}/{new_scores['total_written_questions']}")
                    print(f"    Vision: {new_scores['correct_vision_answers']}/{new_scores['total_vision_questions']}")
        except Exception as e:
            print(f"Error processing {result_file}: {str(e)}")
    
    print("\nSummary:")
    print("--------")
    print(f"Total files affected: {len(affected_files)}")
    print(f"Total attempts at list question: {total_attempts}")
    print(f"Correct list answers: {correct_answers}")
    print(f"Files with fixed question totals: {fixed_totals}")

if __name__ == "__main__":
    main()
