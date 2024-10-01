"""
Reproducability Agent Benchmark
"""
import json
import os
import argparse
from benchmark.benchmark import CodeOceanBenchmark

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment_name", type=str, required=True)
    parser.add_argument("--benchmark_level", type=str, choices=json.load(open("benchmark/benchmark_prompts.json", "r")).keys(), default="codeocean_hard", help="Specifies prompt to use for type of experiment.")
    parser.add_argument("--dataset_file", type=str, default="benchmark/dataset/core_test.json", help="JSON file containing ground-truth capsule results for all tasks in benchmark.")
    parser.add_argument("--agent_dir", type=str, default="agents/AutoGPT-CORE", help="Directory containing agent code.")
    parser.add_argument("--agent_script", type=str, default="coreagent_hard_gpt4o.sh", help="Script to execute within agent directory")
    parser.add_argument("--resume_path", type=str, default=None, help="Experiment results filename to resume from.")
    parser.add_argument("--include_correct_result_paths", action="store_true", help="Includes a file containing the correct result paths of the results directory in each task to provide signal of correctness to the agent.")
    
    parser.add_argument("--platform", type=str, default="local", help="Platform to run the benchmark on")
    parser.add_argument("--no_gpu", action="store_true", help="Skip tasks that require a GPU")
    parser.add_argument("--task_limit", type=int, default=None, help="Limit the number of tasks to run")
    parser.add_argument("--keep_vm", action="store_true", help="Do not delete the Azure VM after running the benchmark")
    parser.add_argument("--keep_temp_envs", action="store_true", help="Keep the downloaded environment after running the benchmark")
    parser.add_argument("--verbose", action="store_true", help="Print output of the benchmark")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()

    # Run benchmark    
    benchmark = CodeOceanBenchmark(args.experiment_name,
                                   args.benchmark_level,
                                   args.dataset_file, 
                                   dataset_dir = os.path.join(os.getcwd(), "benchmark", "dataset"),
                                   agent_dir = args.agent_dir,
                                   agent_script = args.agent_script,
                                   exp_results_dir = os.path.join(os.getcwd(), "benchmark", "results"),
                                   exp_log_dir = os.path.join(os.getcwd(), "benchmark", "logs"),
                                   resume_results_path = args.resume_path,
                                   platform = args.platform,
                                   delete_vm = not args.keep_vm,
                                   print_output = args.platform == "local",
                                   no_gpu = args.no_gpu,
                                   task_limit = args.task_limit,
                                   delete_envs = not args.keep_temp_envs,
                                   include_correct_result_paths = args.include_correct_result_paths,
                                   verbose = args.verbose)
    
    benchmark.run()