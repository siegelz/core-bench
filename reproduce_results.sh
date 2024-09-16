# This script contains the commands to reproduce all experiments in the CORE-Bench paper. In total, ten different experiments were ran. The commands can be ran concurrently, although you might hit Azure rate limit errors.

# ------- Experiments on Train Set -------
# 1) AutoGPT with GPT-4o
python3 main.py --experiment_name "train_autogpt_gpt4o_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --use_azure
python3 main.py --experiment_name "train_autogpt_gpt4o_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --use_azure
python3 main.py --experiment_name "train_autogpt_gpt4o_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --use_azure

# 2) AutoGPT with GPT-4o-mini
python3 main.py --experiment_name "train_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --use_azure
python3 main.py --experiment_name "train_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --use_azure
python3 main.py --experiment_name "train_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --use_azure

# 3) CORE-Agent with GPT-4o
python3 main.py --experiment_name "train_coreagent_gpt4o_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_easy_gpt4o.sh" --use_azure
python3 main.py --experiment_name "train_coreagent_gpt4o_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_medium_gpt4o.sh" --use_azure
python3 main.py --experiment_name "train_coreagent_gpt4o_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o.sh" --use_azure

# 4) CORE-Agent with GPT-4o-mini
python3 main.py --experiment_name "train_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_easy_gpt4o-mini.sh" --use_azure
python3 main.py --experiment_name "train_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_medium_gpt4o-mini.sh" --use_azure
python3 main.py --experiment_name "train_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o-mini.sh" --use_azure

# 5) CoreAgent with GPT-4o (Cost Ablation)
python3 main.py --experiment_name "train_coreagent_gpt4o_c-10" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o_cost_10.sh" --use_azure

# 6) CoreAgent with GPT-4o-mini (Cost Ablation)
python3 main.py --experiment_name "train_coreagent_gpt4o-mini_c-10" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o-mini_cost_10.sh" --use_azure

# ------- Experiments on Test Set -------
# 7) AutoGPT with GPT-4o
python3 main.py --experiment_name "test_autogpt_gpt4o_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --use_azure
python3 main.py --experiment_name "test_autogpt_gpt4o_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --use_azure
python3 main.py --experiment_name "test_autogpt_gpt4o_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --use_azure

# 8) AutoGPT with GPT-4o-mini
python3 main.py --experiment_name "test_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --use_azure
python3 main.py --experiment_name "test_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --use_azure
python3 main.py --experiment_name "test_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --use_azure

# 9) CORE-Agent with GPT-4o
python3 main.py --experiment_name "test_coreagent_gpt4o_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_easy_gpt4o.sh" --use_azure
python3 main.py --experiment_name "test_coreagent_gpt4o_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_medium_gpt4o.sh" --use_azure
python3 main.py --experiment_name "test_coreagent_gpt4o_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o.sh" --use_azure

# 10) CORE-Agent with GPT-4o-mini
python3 main.py --experiment_name "test_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_easy_gpt4o-mini.sh" --use_azure
python3 main.py --experiment_name "test_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_medium_gpt4o-mini.sh" --use_azure
python3 main.py --experiment_name "test_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o-mini.sh" --use_azure