#!/bin/bash
SCRIPT_DIR=$(dirname "$0")

# install google chrome for selenium commands of autogpt
sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt -y --fix-broken install

# setup AutoGPT
sudo apt install pipx -y
pipx install poetry
export PATH="/root/.local/bin:$PATH"
mv environment autogpt/environment
cd autogpt

# WORKAROUND: Run the agent to trigger setup (this will fail but we are restarting the agent later)
. autogpt.sh run --ai-task "Write the current temperature in Princeton to a txt file. Create a file report.json file in your workspace and write some random content in it." --ai-name . --skip-reprompt --continuous --log-level DEBUG

sudo poetry install

# Install additional dependencies that are in conflict with poetry but still work
source $(poetry env info --path)/bin/activate
pip install duckduckgo_search httpx -U
pip install weave==0.50.5

# Run the agent
# . autogpt.sh run --ai-task "generate an image of a ball and query the vision language model to describe the image. Save a report.json file with the description as content." --ai-name . --skip-reprompt --continuous --log-level DEBUG