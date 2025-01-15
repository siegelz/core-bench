import json
import argparse
import datetime
import os
import glob
from collections import defaultdict
import re

from weave_utils import get_weave_calls
import weave

# Dictionary mapping directory names to agent names
AGENT_NAME_MAPPING = {
    "test_autogpt_gpt4o_c-4": "AutoGPT (gpt-4o-2024-05-13)",
    "test_autogpt_gpt4o-mini_c-4": "AutoGPT (gpt-4o-mini-2024-07-18)",
    "test_coreagent_claude_35_sonnet_c-4": "CORE-Agent (claude-3.5-sonnet-2024-10-22)",
    "test_coreagent_gpt4o_c-4": "CORE-Agent (gpt-4o-2024-05-13)",
    "test_coreagent_gpt4o-mini_c-4": "CORE-Agent (gpt-4o-mini-2024-07-18)",
    "test_coreagent_o1-mini_c-10": "CORE-Agent (o1-mini-2024-09-12)",
}

PROMPT_TOKEN_COST = {
    "claude-3-5-sonnet-20241022": 3 / 1_000_000,
    "gpt-4o-2024-05-13": 5 / 1_000_000,
    "gpt-4o-mini-2024-07-18": 0.150 / 1_000_000,
    "o1-mini-2024-09-12": 3 / 1_000_000,
}

COMPLETION_TOKEN_COST = {
    "claude-3-5-sonnet-20241022": 15 / 1_000_000,
    "gpt-4o-2024-05-13": 15 / 1_000_000,
    "gpt-4o-mini-2024-07-18": 0.6 / 1_000_000,
    "o1-mini-2024-09-12": 12 / 1_000_000,
}

def get_benchmark_name(filename):
    """Determine benchmark name based on file content"""
    filename_lower = filename.lower()
    if "hard" in filename_lower:
        benchmark_name = "corebench_hard"
    elif "medium" in filename_lower:
        benchmark_name = "corebench_medium"
    else:
        benchmark_name = "corebench_easy"
    return benchmark_name

def standardize_name(name):
    """Convert agent name to standardized format for run_id"""
    # Convert to lowercase
    name = name.lower()
    # Replace spaces and special chars (except hyphens) with underscores
    name = re.sub(r'[^a-z0-9\-]+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name

def get_timestamp_from_filename(filename):
    """Extract timestamp from filename, assuming format contains YYYYMMDD-HHMMSS"""
    match = re.search(r'(\d{8}-\d{6})', filename)
    timestamp = match.group(1) if match else "99999999-999999"  # Default to high value if no timestamp found
    return timestamp

def compute_cost_from_tokens(total_usage):
    """Compute cost using token counts and predefined costs per token"""
    total_cost = 0.0
    for model, usage in total_usage.items():
        if model not in PROMPT_TOKEN_COST or model not in COMPLETION_TOKEN_COST:
            raise ValueError(f"Model {model} not found in token cost dictionaries")
        
        prompt_cost = usage["prompt_tokens"] * PROMPT_TOKEN_COST[model]
        completion_cost = usage["completion_tokens"] * COMPLETION_TOKEN_COST[model]
        total_cost += prompt_cost + completion_cost
    return total_cost

def compute_cost_from_logs(logs_dir, capsule_id):
    """Compute cost from log files (deprecated method)"""
    cost = 0.0
    log_file_path = os.path.join(logs_dir, f"{capsule_id}.log")
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r') as log_file:
                log_data = json.load(log_file)
                cost = log_data.get('cost', 0.0)
        except json.JSONDecodeError:
            pass
    return cost

def process_result_file(result_path, agent_name, date, dataset_path):
    # Get standardized benchmark name
    filename = os.path.basename(result_path)
    benchmark_name = get_benchmark_name(filename)

    # Create output filename using parent directory and original JSON name
    parent_dir = os.path.basename(os.path.dirname(result_path))
    output_filename = f"{parent_dir}_{filename}"
    
    # Use the output filename (without .json) as the run_id
    run_id = os.path.splitext(output_filename)[0]

    client = weave.init(os.path.splitext(os.path.basename(result_path))[0])

    # Read the input JSON file
    with open(result_path, 'r') as f:
        data = json.load(f)

    # Read dataset file
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)

    # Create lookup dict for ground truth
    ground_truth_dict = {item['capsule_id']: item['results'][0].keys() for item in dataset}

    # Process the data
    capsule_results = data.get('capsule_results', [])
    total_tasks = len(capsule_results)
    successful_tasks = []
    failed_tasks = []
    total_cost = 0.0
    attempted_tasks = 0
    raw_eval_results = {}

    # Determine the logs directory based on the result_path
    result_dir = os.path.dirname(os.path.abspath(result_path))
    logs_dir = result_dir.replace(os.sep + 'results' + os.sep, os.sep + 'logs' + os.sep)
    # Extract the subdirectory from the result_path filename
    result_filename = os.path.splitext(os.path.basename(result_path))[0]
    logs_dir = os.path.join(logs_dir, result_filename)

    # Get raw logging results first
    raw_logging_results = get_weave_calls(client)

    # Calculate total usage if raw_logging_results exists and has data
    total_usage = {}
    if raw_logging_results and len(raw_logging_results) > 0:
        for result in raw_logging_results:
            if "summary" in result and "usage" in result["summary"]:
                for model, model_usage in result["summary"]["usage"].items():
                    if model not in total_usage:
                        total_usage[model] = {
                            "prompt_tokens": 0,
                            "completion_tokens": 0
                        }
                    if "claude" in model:
                        total_usage[model]["prompt_tokens"] += model_usage.get("input_tokens", 0)
                        total_usage[model]["completion_tokens"] += model_usage.get("output_tokens", 0)
                    elif "gpt" in model:
                        total_usage[model]["prompt_tokens"] += model_usage.get("prompt_tokens", 0)
                        total_usage[model]["completion_tokens"] += model_usage.get("completion_tokens", 0)

        # Try to compute cost from token usage if we have data
        try:
            if total_usage:
                total_cost = compute_cost_from_tokens(total_usage)
        except ValueError as e:
            print(f"Warning: {str(e)}")
            # Fallback to log-based cost computation
            for capsule in capsule_results:
                total_cost += compute_cost_from_logs(logs_dir, capsule['capsule_id'])
        except Exception as e:
            print(f"Error computing cost from tokens: {str(e)}")
            # Fallback to log-based cost computation
            for capsule in capsule_results:
                total_cost += compute_cost_from_logs(logs_dir, capsule['capsule_id'])
    else:
        # No raw_logging_results or empty, use log-based calculation
        for capsule in capsule_results:
            total_cost += compute_cost_from_logs(logs_dir, capsule['capsule_id'])

    for capsule in capsule_results:
        capsule_id = capsule.get('capsule_id')
        correct_written_answers = capsule.get('correct_written_answers', 0)
        total_written_questions = capsule.get('total_written_questions', 0)
        correct_vision_answers = capsule.get('correct_vision_answers', 0)
        total_vision_questions = capsule.get('total_vision_questions', 0)

        # Store result_report in raw_eval_results
        result_report = capsule.get('result_report', {})
        raw_eval_results[capsule_id] = result_report

        # Check if all questions were attempted
        if capsule_id in ground_truth_dict:
            expected_keys = ground_truth_dict[capsule_id]
            if all(key in result_report for key in expected_keys):
                attempted_tasks += 1

        # Determine success or failure
        if (correct_written_answers == total_written_questions) and (correct_vision_answers == total_vision_questions):
            successful_tasks.append(capsule_id)
        else:
            failed_tasks.append(capsule_id)

    accuracy = round(len(successful_tasks) / total_tasks, 4) if total_tasks > 0 else 0
    attempted_rate = round(attempted_tasks / total_tasks, 4) if total_tasks > 0 else 0

    # Build the output JSON
    output_data = {
        "config": {
            "agent_name": agent_name,
            "benchmark_name": benchmark_name,
            "date": date,
            "run_id": run_id
        },
        "results": {
            "accuracy": accuracy, # Success rate of correctly answering all task questions
            "attempted_rate": attempted_rate, # Rate of tasks where all questions were attempted
            "total_cost": total_cost,  # Always include total_cost, even if 0
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks
        },
        "raw_logging_results": raw_logging_results,
        "raw_eval_results": raw_eval_results
    }

    # Add total_usage if it exists
    if total_usage:
        output_data["total_usage"] = total_usage

    # Write the output JSON
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hal_json", output_filename)
    with open(filepath, 'w') as f:
        json.dump(output_data, f, indent=2)

def collect_agent_names(files):
    """Collect agent names for unique parent directories"""
    # Group files by parent directory
    dir_files = defaultdict(list)
    for file_path in files:
        parent_dir = os.path.dirname(file_path)
        dir_files[parent_dir].append(file_path)

    # Collect agent names for each unique directory
    agent_names = {}
    for parent_dir, dir_file_list in dir_files.items():
        dir_name = os.path.basename(parent_dir)
        # Check if directory name exists in the mapping
        if dir_name in AGENT_NAME_MAPPING:
            agent_name = AGENT_NAME_MAPPING[dir_name]
        else:
            agent_name = input(f"What is the agent name for {dir_name}? ")
        
        if agent_name.strip():  # Only store non-empty names
            # Apply the name to all files in this directory
            for file_path in dir_file_list:
                agent_names[file_path] = agent_name

    return agent_names

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process result data and compute accuracy.')
    parser.add_argument('--result_path', help='Path to specific result file. If not provided, processes all files in benchmark/results')
    parser.add_argument('--date', default=datetime.datetime.now().strftime('%Y-%m-%d'), help='Date in YYYY-MM-DD format')
    parser.add_argument('--dataset_path', default='benchmark/dataset/core_test.json', help='Path to dataset file')

    args = parser.parse_args()

    if args.result_path:
        # Single file mode
        files = [args.result_path]
    else:
        # Multiple files mode
        results_dir = 'benchmark/results'
        files = glob.glob(os.path.join(results_dir, '**/*.json'), recursive=True)

    # Collect agent names for all files
    agent_names = collect_agent_names(files)

    # Process all files
    for result_file, agent_name in agent_names.items():
        process_result_file(result_file, agent_name, args.date, args.dataset_path)

if __name__ == '__main__':
    main()
