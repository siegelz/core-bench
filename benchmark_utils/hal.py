import json
import argparse
import datetime
import os

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process result data and compute accuracy.')
    parser.add_argument('--result_path', required=True, help='Path to the input result file')
    parser.add_argument('--agent_name', required=True, help='Agent name')
    parser.add_argument('--benchmark_name', required=True, help='Benchmark name')
    parser.add_argument('--date', default=datetime.datetime.now().strftime('%Y-%m-%d'), help='Date in YYYY-MM-DD format')

    args = parser.parse_args()

    run_id = f"{args.benchmark_name}_{args.agent_name.lower().replace(' ', '_').replace('.', '_').replace('(', '').replace(')', '')}_{args.date.replace('-', '')}"

    # Read the input JSON file
    with open(args.result_path, 'r') as f:
        data = json.load(f)

    # Process the data
    capsule_results = data.get('capsule_results', [])
    total_tasks = len(capsule_results)
    successful_tasks = []
    failed_tasks = []
    total_cost = 0.0

    # Determine the logs directory based on the result_path
    result_dir = os.path.dirname(os.path.abspath(args.result_path))
    logs_dir = result_dir.replace(os.sep + 'results' + os.sep, os.sep + 'logs' + os.sep)
    # Extract the subdirectory from the result_path filename
    result_filename = os.path.splitext(os.path.basename(args.result_path))[0]
    logs_dir = os.path.join(logs_dir, result_filename)

    for capsule in capsule_results:
        capsule_id = capsule.get('capsule_id')
        correct_written_answers = capsule.get('correct_written_answers', 0)
        total_written_questions = capsule.get('total_written_questions', 0)
        correct_vision_answers = capsule.get('correct_vision_answers', 0)
        total_vision_questions = capsule.get('total_vision_questions', 0)

        # Determine success or failure
        if (correct_written_answers == total_written_questions) and (correct_vision_answers == total_vision_questions):
            successful_tasks.append(capsule_id)
        else:
            failed_tasks.append(capsule_id)

        # Try to read the cost from the .log file
        log_file_path = os.path.join(logs_dir, f"{capsule_id}.log")
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, 'r') as log_file:
                    log_data = json.load(log_file)
                    cost = log_data.get('cost', None)
                    if cost is not None:
                        total_cost += cost
            except json.JSONDecodeError:
                pass  # Ignore JSON decoding errors
        else:
            pass  # File does not exist; cost remains unchanged

    accuracy = round(len(successful_tasks) / total_tasks, 4) if total_tasks > 0 else 0

    # Build the output JSON
    output_data = {
        "config": {
            "agent_name": args.agent_name,
            "benchmark_name": args.benchmark_name,
            "date": args.date,
            "run_id": run_id
        },
        "results": {
            "accuracy": accuracy,
            "total_cost": total_cost if total_cost > 0 else None,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks
        }
    }

    # Write the output JSON
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{run_id}.json")
    with open(filepath, 'w') as f:
        json.dump(output_data, f, indent=2)

if __name__ == '__main__':
    main()