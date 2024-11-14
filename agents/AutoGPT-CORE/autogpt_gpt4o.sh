#!/bin/bash
SCRIPT_DIR=$(dirname "$0")

# Read in task.txt from SCRIPT_DIR/environment/
task_prompt=$(cat $SCRIPT_DIR/environment/task.txt)

echo 'Installing dependencies...'

# Install dependencies
sudo apt update
sudo apt install -y python3-pip

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
sudo apt install pipx -y
pipx install poetry
export PATH="/root/.local/bin:$PATH"
mv environment autogpt/environment
cd autogpt

# get capsule id from subdirectory name in environment folder
cap_subdir=$(find ./environment -maxdepth 1 -type d -name "cap*" -exec basename {} \;)
echo "$cap_subdir"

# create symbolic links for /code, /data, and /results
sudo ln -s $(pwd)/environment/$cap_subdir/code /code
sudo ln -s $(pwd)/environment/$cap_subdir/data /data
sudo ln -s $(pwd)/environment/$cap_subdir/results /results

# Run the agent
. autogpt.sh run --ai-task "$task_prompt" --ai-name "$cap_subdir" --skip-reprompt --continuous --log-level DEBUG --vlm "gpt-4o-2024-05-13" --fast_llm "gpt-4o-2024-05-13" --smart_llm "gpt-4o-2024-05-13" --openai_cost_budget 4

cd ..
mv autogpt/environment .