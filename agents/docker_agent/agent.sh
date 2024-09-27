#!/bin/bash
SCRIPT_DIR=$(dirname "$0")

log_file="agent_trace.log"

# Install dependencies
sudo apt update
sudo apt install -y python3-pip
pip3 install -r $SCRIPT_DIR/requirements.txt

# Install Docker
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker $(whoami)

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

# Define the file name
cap_subdir=$(find ./environment -maxdepth 1 -type d -name "cap*" -exec basename {} \;)
file="environment/$cap_subdir/REPRODUCING.md"

# Extract the command between the ```shell``` block
command=$(sed -n '/```shell/,/```/p' "$file" | sed -e '1d;$d')

echo "Running command: $command" | tee -a $log_file

# Run the extracted command with a timeout, log output to file, and display on stdout
sudo bash -c "cd 'environment/$cap_subdir' && timeout 7500 $command" 2>&1 | tee -a $log_file