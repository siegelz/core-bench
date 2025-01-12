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

curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.10

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

sudo -E bash autogpt.sh run --ai-task "Please install R script using apt-get (but without sudo) and test it." --ai-name "$cap_subdir" --skip-reprompt --continuous --log-level DEBUG --vlm "gpt-4o-2024-05-13" --fast_llm "claude-3-5-sonnet-20241022" --smart_llm "claude-3-5-sonnet-20241022"  --openai_cost_budget 4

sleep infinity

cd ..
mv autogpt/environment .
