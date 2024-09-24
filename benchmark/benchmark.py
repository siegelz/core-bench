import json
import os
import queue
import re
import shutil
import docker
import time
import concurrent.futures
from azure_utils.vm_manager import VirtualMachineManager
from filelock import FileLock
import urllib.request
import tarfile

from benchmark.evaluations import eval_result_json, score_results

class CodeOceanTask:
    def __init__(self, task_json, dataset_dir):
        self.__validate_json(task_json)

        # Load the task information
        self.field = task_json["field"]
        self.language = task_json["language"]
        self.capsule_title = task_json["capsule_title"]
        self.capsule_id = task_json["capsule_id"]
        self.task_prompt = task_json["task_prompt"]
        self.results = task_json["results"]

        # Download the capsule environment if it doesn't exist
        self.dataset_dir = dataset_dir
        self.__download_and_extract_capsule()

        # Load the result paths
        self.result_paths = [x for x in os.walk(os.path.join(self.dataset_dir, self.capsule_id, "results"))]

        # Check if the task uses a GPU and get the registry link
        self.uses_gpu = False
        with open(os.path.join(self.dataset_dir, self.capsule_id, "REPRODUCING.md"), "r") as f:
            file = f.read()
            if "gpu" in file:
                self.uses_gpu = True
            
            registry_pattern = r'`(registry\.codeocean\.com/published/[\w-]+:v\d+)`'
            match = re.search(registry_pattern, file)
            self.registry_link = match.group(1) if match else None
    
    def __download_and_extract_capsule(self, max_retries=5, backoff_factor=1):
        """
        Downloads a capsule archive from a specified URL if it doesn't exist,
        extracts it, and deletes the original archive file.
        """
        # Define the path to the capsule directory
        capsule_dir = os.path.join(self.dataset_dir, self.capsule_id)

        # Check if the capsule directory already exists
        if not os.path.exists(capsule_dir):
            # Construct the URL for the capsule archive
            capsule_url = f"https://corebench.cs.princeton.edu/capsules/{self.capsule_id}.tar.gz"
            tar_path = os.path.join(self.dataset_dir, f"{self.capsule_id}.tar.gz")
            
            # Initialize retry variables
            attempt = 0
            while attempt < max_retries:
                try:
                    attempt += 1
                    print(f"[Benchmark] Downloading {capsule_url} to {tar_path}...")
                    urllib.request.urlretrieve(capsule_url, tar_path)
                    break  # Exit the loop if download is successful
                except Exception as e:
                    print(f"[Benchmark] Error downloading {capsule_url} on attempt {attempt}: {e}")
                    if attempt == max_retries:
                        print("[Benchmark] Maximum download attempts reached. Raising exception.")
                        raise  # Re-raise the exception after final attempt
                    else:
                        sleep_time = backoff_factor * (2 ** (attempt - 1))  # Exponential backoff
                        print(f"[Benchmark] Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)

            try:
                # Extract the downloaded .tar.gz file
                with tarfile.open(tar_path, "r:gz") as tar:
                    tar.extractall(path=self.dataset_dir)
            except Exception as e:
                print(f"[Benchmark] Error extracting {tar_path}: {e}")
                raise  # Re-raise the exception after logging

            try:
                # Delete the original .tar.gz file after extraction
                os.remove(tar_path)
            except Exception as e:
                print(f"[Benchmark] Error deleting {tar_path}: {e}")
                raise  # Re-raise the exception after logging

    def __validate_json(self, task_json):
        assert task_json.keys() == {"field", "language", "capsule_title", "capsule_id", "capsule_doi", "task_prompt", "results"}, f"Invalid task json keys: {task_json.keys()}"
        assert type(task_json["field"]) == str, f"Field is not a string: {task_json['field']}"
        assert type(task_json["language"]) == str, f"Language is not a string: {task_json['language']}"
        assert type(task_json["capsule_title"]) == str, f"Capsule title is not a string: {task_json['capsule_title']}"
        assert type(task_json["capsule_id"]) == str, f"Capsule id is not a string: {task_json['capsule_id']}"
        assert type(task_json["capsule_doi"]) == str, f"Capsule DOI is not a string: {task_json['capsule_doi']}"
        assert type(task_json["task_prompt"]) == str, f"Task prompt is not a string: {task_json['task_prompt']}"
        assert type(task_json["results"]) == list, f"Capsule results is not a list: {task_json['results']}"
        for result in task_json["results"]:
            assert type(result) == dict, f"Each capsule result is not a dictionary: {result}"
            assert result.keys() == task_json["results"][0].keys(), f"Capsule results have different keys: {result}"

    def check_result_paths(self, result_paths):
        gt_files = [file for _, _, files in self.result_paths for file in files]
        report_files = [file for _, _, files in result_paths for file in files]
        for filepath in gt_files:
            if filepath not in report_files and filepath != 'output': return False
        return True

class CodeOceanBenchmark:
    def __init__(self, experiment_name, benchmark_level, dataset_results_path, dataset_dir, agent_dir, agent_script, exp_results_dir, exp_log_dir, resume_results_path = None, use_azure = False, delete_vm = True, print_output = True, no_gpu = False, task_limit = None, delete_envs = False, include_correct_result_paths = False):
        self.experiment_name = experiment_name
        self.benchmark_level = benchmark_level
        self.dataset_results_path = dataset_results_path
        self.dataset_dir = dataset_dir
        self.agent_dir = agent_dir
        self.agent_script = agent_script
        self.exp_results_dir = exp_results_dir
        self.exp_log_dir = exp_log_dir
        self.resume_results_path = resume_results_path
        self.use_azure = use_azure
        self.delete_vm = delete_vm
        self.print_output = print_output
        self.timestamp = time.strftime('%Y%m%d-%H%M%S', time.localtime())
        self.no_gpu = no_gpu
        self.task_limit = task_limit
        self.delete_envs = delete_envs
        self.include_correct_result_paths = include_correct_result_paths

        if self.resume_results_path:
            assert os.path.exists(self.resume_results_path), "Resume results path does not exist."
            assert os.path.splitext(os.path.basename(self.resume_results_path))[0].split("_", 1)[1] == self.benchmark_level, "Benchmark name in resume results path does not match benchmark name."
            self.timestamp = os.path.splitext(os.path.basename(self.resume_results_path))[0].split("_")[0]

        if self.use_azure:
            self.VMM = VirtualMachineManager()

        if benchmark_level not in ['codeocean_easy', 'codeocean_medium', 'codeocean_hard']:
            raise ValueError(f"Invalid benchmark name: {benchmark_level}.")
    
    def __find_report_path(self, env_path):
        for root, _, files in os.walk(env_path):
            for file in files:
                if file == "report.json":
                    return os.path.join(root, file)
        return None

    def __write_task_result(self, task, result_report, result_paths):
        # Create results json if filepath doesn't exist, including all directories along the way
        results_filepath = os.path.join(self.exp_results_dir, self.experiment_name, f"{self.timestamp}_{self.benchmark_level}.json")
        if not os.path.exists(results_filepath):
            os.makedirs(os.path.dirname(results_filepath), exist_ok = True)
            with open(results_filepath, "w") as f:
                json.dump({'capsule_results': []}, f, indent = 4)

        # Open results json
        lock = FileLock(f"{results_filepath}.lock")
        with lock:
            with open(results_filepath, "r") as f:
                results = json.load(f)

        # Evaluate the results
        dataset = json.load(open(self.dataset_results_path, "r"))
        gt_result = None
        for capsule in dataset:
            if capsule["capsule_id"] == task.capsule_id:
                gt_result = capsule["results"]
                break
        evals = eval_result_json(gt_result, result_report)

        # Update results json
        capsule_result = {
            "field": task.field,
            "language": task.language,
            "capsule_title": task.capsule_title,
            "capsule_id": task.capsule_id,
            "result_report": result_report,
            "result_paths": [file for _, _, files in result_paths for file in files],
            "result_paths_success": task.check_result_paths(result_paths),
        }
        capsule_result.update(evals)
        results['capsule_results'].append(capsule_result)

        # Write to results json
        with lock:
            with open(results_filepath, "w") as f:
                json.dump(results, f, indent = 4)

    def __write_task_log(self, task, log_contents):
        output_log_path = os.path.join(self.exp_log_dir, self.experiment_name, f"{self.timestamp}_{self.benchmark_level}", f"{task.capsule_id}.log")
        os.makedirs(os.path.dirname(output_log_path), exist_ok=True)
        with open(output_log_path, "w") as file:
            file.write(log_contents)

    def __setup_task_environment(self, task):
        # Copy agent directory to temporary directory
        task_path = os.path.join("benchmark", "temp_envs", self.experiment_name, f"{task.capsule_id}-{self.timestamp}")
        os.makedirs(task_path, exist_ok = True)
        shutil.rmtree(task_path)
        shutil.copytree(self.agent_dir, task_path)

        # Copy capsule to environment
        task_env_path = os.path.join(task_path, "environment")
        task_capsule_path = os.path.join(task_env_path, task.capsule_id)
        os.makedirs(task_env_path, exist_ok = True)
        shutil.copytree(os.path.join(self.dataset_dir, task.capsule_id), os.path.join(task_env_path, task.capsule_id))

        # Remove files depending on task difficulty
        if self.benchmark_level != "codeocean_easy":
            task_results_path = os.path.join(task_capsule_path, "results")
            shutil.rmtree(task_results_path)
            os.makedirs(task_results_path, exist_ok = True)
        if self.benchmark_level != "codeocean_medium":
            # Remove the REPRODUCING.md file
            os.remove(os.path.join(task_capsule_path, "REPRODUCING.md"))

            # Remove the environment directory
            shutil.rmtree(os.path.join(task_capsule_path, "environment"))

            # Remove runfile scripts
            if os.path.exists(os.path.join(task_capsule_path, "code", "run.sh")):
                os.remove(os.path.join(task_capsule_path, "code", "run.sh")) 
            if os.path.exists(os.path.join(task_capsule_path, "code", "run")):
                os.remove(os.path.join(task_capsule_path, "code", "run"))
        
        # Add the result paths
        if self.include_correct_result_paths:
            result_paths_str = '\n'.join([file for _, _, files in task.result_paths for file in files])
            with open(os.path.join(task_env_path, "correct_result_paths.txt"), "w") as f:
                f.write(result_paths_str)

        # Add the task prompt
        task_str = json.load(open("benchmark/benchmark_prompts.json", "r"))[self.benchmark_level]
        task_str = task_str.replace("{task_prompt}", task.task_prompt)
        task_str = task_str.replace("{json_fields}", str(task.results[0].keys()))
        task_str = task_str.replace("{registry_link}", task.registry_link)
        with open(os.path.join(task_env_path, "task.txt"), "w") as f:
            f.write(task_str)

    """
    Creates a Docker container, copies the environment and agent to the container, runs the agent,
    and copies the results back for evaluation overwriting the task_path.
    """
    def __run_agent_local(self, task, image_name = 'ubuntu:jammy', timeout=8100, verbose=True):
        # Path to environment in temp_envs
        task_path = os.path.join("benchmark", "temp_envs", self.experiment_name, f"{task.capsule_id}-{self.timestamp}")

        # Create Docker container
        print(f"[Benchmark] Creating Docker container for {task.capsule_id}")
        
        client = docker.from_env()
        client.images.pull(image_name)
        container = client.containers.create(
            image = image_name,
            command = 'sleep infinity',
        )
        container.start()
        container.exec_run("apt update")
        container.exec_run("apt install -y sudo")
        container.exec_run("bash -c 'echo \"export DEBIAN_FRONTEND=noninteractive\" >> /root/.bashrc'")

        try:
            print(f"[Benchmark] Copying files to Docker container {container.id}")

            # Create a tar archive of the environment
            with tarfile.open(f"{task_path}.tar", "w") as tar:
                tar.add(task_path, arcname=os.path.basename(task_path))

            # Copy the tar to Docker container
            with open(f"{task_path}.tar", "rb") as f:
                container.put_archive(f"/", f)

            shutil.rmtree(task_path)
            os.remove(f"{task_path}.tar")

            print(f"[Benchmark] Running agent on Docker container {container.id}")

            # Run agent in Docker container
            docker_task_path = f"/{os.path.basename(task_path)}"
            container.exec_run(f"bash -c '(timeout {timeout} bash {docker_task_path}/{self.agent_script}) > {docker_task_path}/output.log 2>&1 ; touch {docker_task_path}/task_completed.log'")

            if verbose:
                output = container.exec_run(f"cat {docker_task_path}/output.log")
                print(f"\n{output.output.decode('utf-8')}")

            print(f"[Benchmark] Copying files from Docker container {container.id}")

            # Copy results back to temp_envs
            stream, _ = container.get_archive(f"{docker_task_path}")
            with open(f"{task_path}.tar", "wb") as f:
                for chunk in stream:
                    f.write(chunk)

            with tarfile.open(f"{task_path}.tar", "r") as tar:
                tar.extractall(path=os.path.dirname(task_path))
            os.remove(f"{task_path}.tar")
        except KeyboardInterrupt:
            print(f"[Benchmark] Attempting to gracefully exit and clean up Docker container {container.id}")
        finally:
            container.stop()
            container.remove()

    def __eval_agent_local(self, task):
        task_path = os.path.join("benchmark", "temp_envs", self.experiment_name, f"{task.capsule_id}-{self.timestamp}")
        
        # Log the agent debug output
        log_contents = open(os.path.join(task_path, "task_completed.log"), "r").read()
        self.__write_task_log(task, log_contents)

        # Evaluate the agent and log results
        task_env_path = os.path.join(task_path, "environment")
        task_capsule_path = os.path.join(task_env_path, task.capsule_id)
        try:
            if self.__find_report_path(task_env_path) is not None:
                result_report = json.load(open(self.__find_report_path(task_env_path)))
            else:
                result_report = {}
        except:
            result_report = {}

        self.__write_task_result(
            task = task,
            result_report = result_report,
            result_paths = [x for x in os.walk(os.path.join(task_capsule_path, "results"))]
        )

    def __start_agent_vm(self, task):
        from config import SSH_PUBLIC_KEY_PATH, SSH_PRIVATE_KEY_PATH, NETWORK_SECURITY_GROUP_NAME
        task_path = os.path.join("benchmark", "temp_envs", self.experiment_name, f"{task.capsule_id}-{self.timestamp}")

        # Set up environment locally
        self.__setup_task_environment(task)

        # Create the Azure VM 
        for attempt in range(5):
            try:
                if task.uses_gpu:
                    print(f"[Benchmark] Creating GPU VM for {task.capsule_id}...")
                    self.VMM.create_gpu_vm(
                        vm_name = f"{task.capsule_id}-{self.timestamp}",
                        username = "crab",
                        ssh_public_key_path = SSH_PUBLIC_KEY_PATH,
                        network_security_group_name = NETWORK_SECURITY_GROUP_NAME
                    )
                else:
                    print(f"[Benchmark] Creating standard VM for {task.capsule_id}...")
                    self.VMM.create_vm(
                        vm_name = f"{task.capsule_id}-{self.timestamp}",
                        username = "crab",
                        ssh_public_key_path = SSH_PUBLIC_KEY_PATH,
                        network_security_group_name = NETWORK_SECURITY_GROUP_NAME
                    )
                break
            except Exception as e:
                if attempt == 4: raise Exception(f"Failed to create VM for {task.capsule_id}: {e}")
                print(f"[Benchmark] Error thrown while creating VM: {e}")
                time.sleep(10)

        time.sleep(10)

        # Copy the environment to Azure
        print(f"[Benchmark] Copying files to the VM for {task.capsule_id}...")
        for attempt in range(5):
            try:
                self.VMM.copy_files_to_vm(
                    source_directory = task_path,
                    vm_name = f"{task.capsule_id}-{self.timestamp}",
                    username = "crab",
                    ssh_private_key_path = SSH_PRIVATE_KEY_PATH,
                )
                break
            except Exception as e:
                if attempt == 4: raise Exception(f"Failed to copy files to VM for {task.capsule_id}: {e}")
                time.sleep(10)

        # Start the agent on Azure
        print(f"[Benchmark] Running the agent on the VM for {task.capsule_id}...")
        for attempt in range(5):
            try:
                self.VMM.run_agent_on_vm(
                    agent_script = self.agent_script,
                    vm_name = f"{task.capsule_id}-{self.timestamp}",
                    username = "crab",
                    ssh_private_key_path = SSH_PRIVATE_KEY_PATH,
                )
                break
            except Exception as e:
                if attempt == 4: raise Exception(f"Failed to run agent on VM for {task.capsule_id}: {e}")
                time.sleep(10)

    def __eval_agent_vm(self, task):
        try:
            from config import SSH_PRIVATE_KEY_PATH
            task_path = os.path.join("benchmark", "temp_envs", self.experiment_name, f"{task.capsule_id}-{self.timestamp}")

            for attempt in range(5):
                try:
                    log_contents = self.VMM.check_task_completion(
                        vm_name = f"{task.capsule_id}-{self.timestamp}",
                        username = "crab",
                        ssh_private_key_path = SSH_PRIVATE_KEY_PATH,
                        filename = "task_completed.log"
                    )
                    break
                except Exception as e:
                    if attempt == 4: raise Exception(f"Failed to check task completion on VM for {task.capsule_id}: {e}")
                    time.sleep(10)
            if log_contents is None:
                raise Exception(f"Agent is not finished on {task.capsule_id}")

            # Write the log contents to a file
            self.__write_task_log(task, log_contents)

            # Copy the results back to the local machine
            print(f"[Benchmark] Copying files from the VM for {task.capsule_id}...")
            shutil.rmtree(task_path)
            for attempt in range(5):
                try:
                    self.VMM.copy_files_from_vm(
                        destination_directory = task_path,
                        vm_name = f"{task.capsule_id}-{self.timestamp}",
                        username = "crab",
                        ssh_private_key_path = SSH_PRIVATE_KEY_PATH,
                    )
                    break
                except Exception as e:
                    if attempt == 4: raise Exception(f"Failed to copy files from VM for {task.capsule_id}: {e}")
                    time.sleep(10)

            # Evaluate the agent
            task_env_path = os.path.join(task_path, "environment")
            task_capsule_path = os.path.join(task_env_path, task.capsule_id)

            try:
                if self.__find_report_path(task_env_path) is not None:
                    result_report = json.load(open(self.__find_report_path(task_env_path)))
                else:
                    result_report = {}
            except:
                result_report = {}

            self.__write_task_result(
                task = task,
                result_report = result_report,
                result_paths = [x for x in os.walk(os.path.join(task_capsule_path, "results"))]
            )
        except Exception as e:
            print(f"[Benchmark] Evaluation error thrown: {e}")
            return False
        finally:
            pass
            # Delete the Azure VM
            if self.delete_vm:
                print(f"[Benchmark] Deleting the VM for {task.capsule_id}...")
                concurrent.futures.ThreadPoolExecutor().submit(self.VMM.delete_vm, vm_name = f"{task.capsule_id}-{self.timestamp}")

            # Clean up
            if self.delete_envs:
                task_path = os.path.join("benchmark", "temp_envs", self.experiment_name, f"{task.capsule_id}-{self.timestamp}")
                shutil.rmtree(task_path)

    def run(self):
        tasks = []
        task_count = 0
        while len(tasks) < self.task_limit:
            task = CodeOceanTask(json.load(open(self.dataset_results_path, "r"))[task_count], self.dataset_dir)
            task_count += 1

            # Skip tasks that require a GPU
            if self.no_gpu and task.uses_gpu:
                continue

            # Skip tasks that are already in the results
            if self.resume_results_path is not None:
                if not os.path.exists(self.resume_results_path):
                    raise Exception(f"Resume results path does not exist: {self.resume_results_path}")
                if task.capsule_id in [result["capsule_id"] for result in json.load(open(self.resume_results_path, "r"))['capsule_results']]:
                    continue

            tasks.append(task)

        if self.use_azure:
            from config import SSH_PRIVATE_KEY_PATH

            # Constants
            AGENT_STARTUP_TIMEOUT = 60 * 60 # Max time to wait for a task VM to be created before timing out
            MAX_CONSEC_ATTEMPTS = 10 # Max number of consecutive attempts to download results before giving up
            MAX_WORKERS = 20 # Max number of VMs to concurrently upload/download files from

            print("======== Creating VMs ========\n")

            # Start Azure VMs concurrently
            running_agents = []
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
                    future_to_task = {executor.submit(self.__start_agent_vm, task): task for task in tasks}
                    for future in concurrent.futures.as_completed(future_to_task, timeout = AGENT_STARTUP_TIMEOUT):
                        task = future_to_task[future]
                        try:
                            future.result()
                            running_agents.append(task.capsule_id)
                        except Exception as e:
                            print(f"[Benchmark] Error thrown while starting agent: {e}")
            except concurrent.futures.TimeoutError as e:
                print(f"[Benchmark] Timed out while starting some agents: {e}")
            except Exception as e:
                print(f"[Benchmark] An unexpected error occurred: {e}")

            # Print agents that failed to start
            failed_agents = [{task.capsule_id: "Failed to start VM"} for task in tasks if task.capsule_id not in running_agents]
            if len(failed_agents) > 0:
                print(f"[Benchmark] Failed to start the following agents:")
                for failed_agent in failed_agents:
                    print(failed_agent)
            else:
                print(f"[Benchmark] All agents started successfully!")

            print("\n======== Evaluating Agents ========\n")

            # Evaluate agents on Azure VMs concurrently
            task_queue = queue.Queue()
            for task in tasks:
                task_queue.put(task)
            
            consec_download_fails = {task.capsule_id: 0 for task in tasks}
            futures = []
            with concurrent.futures.ThreadPoolExecutor(max_workers = MAX_WORKERS) as executor:
                while not task_queue.empty():
                    task = task_queue.get()
                    try:
                        # Check if the task has completed
                        log_contents = self.VMM.check_task_completion(
                            vm_name = f"{task.capsule_id}-{self.timestamp}",
                            username = "crab",
                            ssh_private_key_path = SSH_PRIVATE_KEY_PATH,
                            filename = "task_completed.log"
                        )
                        consec_download_fails[task.capsule_id] = 0
                        if log_contents is not None:
                            # The task is completed, so evaluate agent
                            futures.append(executor.submit(self.__eval_agent_vm, task))
                        else:
                            # The task is not completed, so requeue
                            task_queue.put(task)
                    except Exception as e:
                        consec_download_fails[task.capsule_id] += 1
                        print(f"[Benchmark] Failed to download results from {task.capsule_id} on attempt {consec_download_fails[task.capsule_id]}: {e}")
                        if consec_download_fails[task.capsule_id] < MAX_CONSEC_ATTEMPTS:
                            task_queue.put(task)
                        else:
                            print(f"[Benchmark] Deleting the VM for {task.capsule_id}...")
                            failed_agents.append({task.capsule_id: "Failed to download results"})
                            if self.delete_vm:
                                concurrent.futures.ThreadPoolExecutor().submit(self.VMM.delete_vm, vm_name = f"{task.capsule_id}-{self.timestamp}")

                    time.sleep(1)
                    
                # Wait for all tasks to finish
                concurrent.futures.wait(futures)

                # Report failed tasks
                if len(failed_agents) > 0:
                    print(f"\n======= Failed Tasks =======\n")
                    for failed_agent in failed_agents:
                        print(failed_agent)
        else:
            for task in tasks:
                # Set up environment locally
                self.__setup_task_environment(task)

                # Run and evaluate the agent
                self.__run_agent_local(task)
                self.__eval_agent_local(task)

                if self.delete_envs:
                    task_path = os.path.join("benchmark", "temp_envs", self.experiment_name, f"{task.capsule_id}-{self.timestamp}")
                    shutil.rmtree(task_path)

        # Score and print results
        results_filepath = os.path.join(self.exp_results_dir, self.experiment_name, f"{self.timestamp}_{self.benchmark_level}.json")
        score_results(results_filepath, verbose = True)