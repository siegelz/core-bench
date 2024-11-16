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
    parser.add_argument('--run_id', required=True, help='Run ID')
    parser.add_argument('--date', default=datetime.datetime.now().strftime('%Y-%m-%d'), help='Date in YYYY-MM-DD format')

    args = parser.parse_args()

    # Read the input JSON file
    with open(args.result_path, 'r') as f:
        data = json.load(f)

    # Process the data
    capsule_results = data.get('capsule_results', [])
    total_tasks = len(capsule_results)
    successful_tasks = []
    failed_tasks = []

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

    accuracy = round(len(successful_tasks) / total_tasks, 4) if total_tasks > 0 else 0

    # Build the output JSON
    output_data = {
        "config": {
            "agent_name": args.agent_name,
            "benchmark_name": args.benchmark_name,
            "date": args.date,
            "run_id": args.run_id
        },
        "results": {
            "accuracy": accuracy,
            "total_cost": None,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks
        }
    }

    # Write the output JSON
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{args.run_id}.json")
    with open(filepath, 'w') as f:
        json.dump(output_data, f, indent=2)

if __name__ == '__main__':
    main()