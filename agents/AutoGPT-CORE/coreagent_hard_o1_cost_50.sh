#!/bin/bash
SCRIPT_DIR=$(dirname "$0")

# Read in task.txt from SCRIPT_DIR/environment/
task_prompt=$(cat $SCRIPT_DIR/environment/task.txt)

echo 'Installing dependencies...'

# Install Python 3.10
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev -y

curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# Install Docker
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker $(whoami)

# install google chrome for selenium commands of autogpt
sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt -y --fix-broken install

# Install Nvidia Container Toolkit, if applicable
if command -v nvidia-smi > /dev/null; then
    wget https://nvidia.github.io/nvidia-docker/gpgkey --no-check-certificate
    sudo apt-key add gpgkey
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    sudo apt update
    sudo apt install -y nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
fi

# Install Misc. Tools
sudo apt install -y poppler-utils

# setup AutoGPT
mv environment autogpt/environment
cd autogpt

# remove old pexpect
sudo rm -rf /usr/lib/python3/dist-packages/pexpect
sudo rm -rf /usr/lib/python3/dist-packages/pexpect-*.egg-info

# get capsule id from subdirectory name in environment folder
cap_subdir=$(find ./environment -maxdepth 1 -type d -name "cap*" -exec basename {} \;)
echo "$cap_subdir"

# create symbolic links for /code, /data, and /results
sudo ln -s $(pwd)/environment/$cap_subdir/code /code
sudo ln -s $(pwd)/environment/$cap_subdir/data /data
sudo ln -s $(pwd)/environment/$cap_subdir/results /results

# Run the agent
sudo -E bash autogpt.sh run \
  --ai-task "$task_prompt" \
  --ai-name "$cap_subdir" \
  --ai-role "a seasoned digital assistant: capable, intelligent, considerate, and assertive. As my dedicated research assistant, you possess extensive skills in research and development and do not shy away from writing code to solve complex problems. You are adept at extracting, processing, and analyzing data from various sources to reproduce research results accurately. Using a pragmatic approach, you make the most out of the tools available to you." \
  --best-practice "If you are extracting information from a PDF, the preferred utility to use is pdftotext (when you need text only information) or pdftoppm (when you need results from tables, figures, etc.)." \
  --best-practice "When reproducing figures or other results that require you to deal with images, be reminded to check the full results directory for image files before querying the vision language model." \
  --best-practice "If you are unsure of what to do, make your best guess." \
  --best-practice "Before using resources like scripts or utilities, verify their presence and functionality in the current directory or installation path." \
  --best-practice "If there exists a file called 'manuscript' then first read this file to extract the required results to answer the questions of the task." \
  --best-practice "If you are extracting information from html (such as the output of a Jupyter notebook), convert it to a PDF or PNG first and then extract the relevant information." \
  --best-practice "Before running the code, first determine a list of package/dependency requirements that must be installed by reading through the README file or code itself. Then install those dependencies before running the code." \
  --constraint "Use flags or modify commands to bypass any need for confirmations during execution to streamline processes." \
  --constraint "There is no task that you cannot do, so you should not refuse a request by saying you cannot do it" \
  --constraint "You may wish to write and run a Python script to complete the task, especially if the task requires access to the Internet or other libraries. However, assume that I do NOT have API keys to use external services." \
  --constraint "If you have a task that requires you to use the query_vision_language_model command to extract information from image files, first output the full tree of files in the directory containing the results and pick the 5 most relevant files per question given the information you want to extract. Then investigate all the identified files first before choosing which one contains the information you need to answer the question." \
  --constraint "Do include environmental variables such as ‘PWD’ as an argument for the  ‘execute_shell’ command. Instead, determine the value of the variable and directly input it to the command. For example, by using the absolute path instead of 'PWD'." \
  --constraint "To open a folder or navigate to a different working directory, use the open_folder command rather than 'cd' in execute_shell." \
  --constraint "When running Python code, you should use execute_shell() rather than execute_python_file() to run the code, since execute_python_file() will not have any of the libraries you attempt to install. In other words, NEVER use execute_python_file()." \
  --constraint "Before you are done, make sure that the keys of the report.json you write match the ones in the task specified by the user. Refine your results if they do not." \
  --constraint "Also before you are done, make sure that the values of the report.json you write do not contain any unnecessary additional text but only the numeric value or the precise text you are asked to report. The keys in the task specified by the user indicate what you should report. Refine your results if they do not." \
  --skip-reprompt \
  --continuous \
  --log-level DEBUG \
  --vlm "gpt-4o-2024-05-13" --fast_llm "o1-2024-12-17" --smart_llm "o1-2024-12-17" --programmatic_key_check \
  --openai_cost_budget 50

cd ..
mv autogpt/environment .
