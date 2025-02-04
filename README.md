<p align="center">
    <a href="https://arxiv.org/abs/2409.11363">
    <img alt="Paper" src="https://img.shields.io/badge/arXiv-arXiv:2409.11363-b31b1b.svg">
    <a href = "https://agent-evals-leaderboard.hf.space">
    <img alt="Leaderboard" src="https://img.shields.io/badge/Leaderboard-Link-blue.svg">
    <a href = "https://github.com/siegelz/core-bench">
    <img alt="GitHub" src="https://img.shields.io/badge/GitHub-Repository-181717.svg">
    <a href="https://huggingface.co/datasets/siegelz/core-bench">
    <img alt="Dataset" src="https://img.shields.io/badge/Hugging%20Face-Dataset-yellow.svg">
</p>

# CORE-Bench Overview
`CORE-Bench` is a benchmark for evaluating the ability of agents to computationally reproduce scientific papers. It comprises 270 tasks from 90 papers across computer science, social science, and medicine, written in Python or R.

To successfully complete a task, the agent must read the task prompt and questions, navigate through the code repository to install dependencies, run the code to genereate results, and read through the code results to answer the task questions.

![Local Image](./images/benchmark_overview.png)

You can find the CORE-Bench [paper here](https://arxiv.org/abs/2409.11363) and view the [dataset here](https://huggingface.co/datasets/siegelz/core-bench).

## Harness Description
This harness allows you to easily evaluate your own agents, or the `AutoGPT` and `CORE-Bench` agents, on the `CORE-Bench` dataset. The harness runs agents in an isolated environment (either locally in a Docker container or on an Azure VM). The harness also provides a simple interface for adding new agents to the benchmark.

If you are interested in generating figures and tables from the `CORE-Bench` paper, please see the `benchmark/paper_figures.ipynb` notebook.

## Leaderboard
The `CORE-Bench` leaderboard is hosted through the [Holistic Agent Leaderboard](https://agent-evals-leaderboard.hf.space). For instructions on submitting agents to the leaderboard, please see the [Submitting Agents to the HAL Leaderboard](#submitting-agents-to-the-hal-leaderboard) section.

# Installation and Setup
The harness has been tested with Python 3.9. Clone the repository and install the required packages:
```bash
git clone https://github.com/siegelz/core-bench.git && cd core-bench
conda create --name core-bench python=3.9
conda activate core-bench
pip3 install -r requirements.txt
```

Next, you will need to decrypt `benchmark/dataset/core_test.json.gpg` to access the `CORE-Bench` test set. The password for the GPG file is `reproducibility`. To decrypt the file, run the following command:
```bash
gpg --output benchmark/dataset/core_test.json --decrypt benchmark/dataset/core_test.json.gpg
```

Note that the dataset JSON files contain the task prompts, task questions, and some other metadata for each task, not the associated code repositories. The harness automatically downloads the code repositories for each task from https://corebench.cs.princeton.edu/capsules/capsule-XXXXXXX.tar.gz, where `XXXXXXX` is the `capsule_id`.

You have two options for running the harness: in a Docker container locally or on an Azure VM. Running on Azure allows you to parrallelize tasks and run the benchmark at scale, but running locally could be easier for testing or development purposes. Please follow the instructions below for your desired setup (or both).

## Local Setup
To run the harness locally, you will need to install Docker. You can find instructions for installing Docker [here](https://docs.docker.com/engine/install/). If you are running on macOS Sequoia, you may also need to [install Rosetta](https://romanzipp.com/blog/maocs-sequoia-docker-resetta-is-only-intended-to-run-silicon) for Docker to work properly. The harness will automatically build a Docker image for each agent-task pair, run the agent in the container, and download the results once the agent has completed the task.

Please note that the harness runs containers with the `--privileged` flag to allow Docker in Docker (necessary for CORE-Bench-Medium) to work.

## Azure Setup ([FAQ here](azure_faq.md))
If you wish to run the harness on Azure to parralelize and ensure standardized hardware for each task, you will need to install and configure the Azure CLI.

First, install the [Azure CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd) and log in to your Azure account by running `azd auth login`.

Next, create a `config.py` file in the root of the repository with Azure credentials and the path to a SSH key (see `config.py.template`). The file should look like this:
```python
AZURE_SUBSCRIPTION_ID = "XXX-XXX-XXX-XXX-XXX"
AZURE_RESOURCE_GROUP_NAME = "XXX"
AZURE_LOCATION = "XXX"
NETWORK_SECURITY_GROUP_NAME = "XXX"
SSH_PUBLIC_KEY_PATH = "/Users/XXX/.ssh/id_rsa.pub"
SSH_PRIVATE_KEY_PATH = "/Users/XXX/.ssh/id_rsa"
```

The harness runs on [Standard_E2as_v5](https://cloudprice.net/vm/Standard_E2as_v5) and [Standard_NC4as_T4_v3](https://cloudprice.net/vm/Standard_NC4as_T4_v3) machine types for non-GPU and GPU tasks, respectively. The harness will automatically create a new VM for each task and delete the VM once the task has been completed.

You may need to [request a quota increase](https://portal.azure.com/#view/Microsoft_Azure_Capacity/QuotaMenuBlade/~/myQuotas) for the `Standard_NC4as_T4_v3` machine type if you plan on running GPU tasks.

For a FAQ on setting up Azure, please see the [Azure FAQ](azure_faq.md). if you are having any trouble, feel free to reach out to us.

# Running the Harness
To run the `AutoGPT` and `CORE-Bench` agents, you will also need to add your OpenAI API keys to the `agents/AutoGPT-CORE/autogpt/.env` file. A template for this file can be found at `agents/AutoGPT-CORE/autogpt/.env.template`.

The following command runs `CORE-Agent` (gpt-4o) on the first task of the test set not requiring a GPU on `CORE-Bench-Hard`. Include the `--platform azure` flag to run tasks on Azure (otherwise, the tasks will run locally in a Docker container).
```bash
python3 main.py \
    --experiment_name test_coreagent_gpt4o_c-4 \
    --agent_dir agents/AutoGPT-CORE \
    --dataset_file benchmark/dataset/core_test.json \
    --no_gpu \
    --task_limit 1 \
    --benchmark_level codeocean_hard \
    --agent_script coreagent_hard_gpt4o.sh \
    --verbose
```

Full details for reproducing the results of the `CORE-Bench` paper can be found in the `reproduce_results.sh` script.

# Developing Your Own Agents
To run your own agent through the harness, create a new directory in the `agents` directory with the name of the agent. The directory should contain a Bash script that that harness can invoke to start the agent, which is specified in the ``--agent_script`` flag (e.g. `coreagent_hard_gpt4o.sh`).

When the harness runs the agent, it will automatically copy all files within the agent directory directly into the base directory. In addition, the harness will create an `environment` directory within the base directory that contains the task prompt and task questions (`task.txt`) and the code repository of the associated task (`capsule-XXXXXXX`).:
```
[agent files]
    coreagent_hard_gpt4o.sh
    main.py
    ...

environment/
    capsule-XXXXXXX/
        code/
        data/
        results/
        ...
    task.txt
```

Therefore, your agent must read the `task.txt` file to get the task prompt and questions and navigate through the `capsule-XXXXXXX` directory to carry out the task.

## `report.json`
Once the agent has completed the task, it should write the answer to a file named `report.json` in the `environment` directory. The keys of the JSON object should be the task questions, and the values should be the answers. For example:
```json
{
    "Report the HyperETA MAPE with no DTW.": 17.374344500709498,
    "Report the HyperETA RMSE with no DTW.": 459.7782074000463,
    "Report the HyperETA MAE with no DTW.": 323.0
}
```

The harness will automatically terminate the task once the `--agent_script` (e.g. `coreagent_hard_gpt4o.sh`) has completed. Therefore, the agent should write the `report.json` file once it has finished the task.

## Debugging and Logging
You are highly encouraged (and required, if you plan to submit your agent to the leaderboard) to use the `weave` library to log all LLM calls and responses. The usage is very simple. Simply import `weave` and wrap all LLM calls your agent makes in the following manner:
```python
import weave

weave.init(os.getenv('WEAVE_PROJECT_NAME'))

def get_llm_response(task_id, **kwargs):
    with weave.attributes({'weave_task_id': os.getenv('WEAVE_TASK_ID')}):
        response = client.chat.completions.create(
            model=kwargs['model_name'],
            messages=[
                {"role": "user", "content": 'test'},
                ],
            max_tokens=2000,
            n=1,
            temperature=1,
        )
    return response
```

The harness automatically sets the `WEAVE_TASK_ID` environment variable.

If you wish to log any additional information (e.g. agent output, debugging information) for the harness to download after the agent has completed the task (for example, while developing the agent), write this information to a file named `agent_trace.log` in the **base directory with the other agent files** (not the `environment` directory).

# Submitting Agents to the HAL Leaderboard
The `CORE-Bench` leaderboard is hosted through the [Holistic Agent Leaderboard](https://agent-evals-leaderboard.hf.space). 

To submit your agent to the leaderboard, first run the agent you wish to submit through the harness. **Make sure you have developed your agent to use Weave to log all LLM calls and responses (see [Debugging and Logging](#debugging-and-logging)).**

Then, run the script `benchmark_utils/hal.py`. This script uses the files in `benchmark/results` and the `weave` logs, to generate the JSON files that can be submitted to the HAL leaderboard. The script will generate a JSON file for each agent run in the `results` directory and save them in the `benchmark_utils/hal_json` directory. You may specify a specific JSON file to convert from the results directory using the `--result_path` flag.

Follow the [instructions here](https://github.com/benediktstroebl/hal-harness/blob/main/README.md#uploading-results) to upload the JSON files to the HAL leaderboard.