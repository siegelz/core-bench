# This script contains the commands to reproduce all experiments in the CORE-Bench paper. In total, ten different experiments were ran. The commands can be ran concurrently, although you might hit Azure rate limit errors.

# ------- Experiments on Train Set -------
# AutoGPT with GPT-4o
python3 main.py --experiment_name "train_autogpt_gpt4o_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --platform azure
python3 main.py --experiment_name "train_autogpt_gpt4o_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --platform azure
python3 main.py --experiment_name "train_autogpt_gpt4o_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --platform azure

# AutoGPT with GPT-4o-mini
python3 main.py --experiment_name "train_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --platform azure
python3 main.py --experiment_name "train_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --platform azure
python3 main.py --experiment_name "train_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --platform azure

# CORE-Agent with GPT-4o
python3 main.py --experiment_name "train_coreagent_gpt4o_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_easy_gpt4o.sh" --platform azure
python3 main.py --experiment_name "train_coreagent_gpt4o_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_medium_gpt4o.sh" --platform azure
python3 main.py --experiment_name "train_coreagent_gpt4o_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o.sh" --platform azure

# CORE-Agent with GPT-4o-mini
python3 main.py --experiment_name "train_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_easy_gpt4o-mini.sh" --platform azure
python3 main.py --experiment_name "train_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_medium_gpt4o-mini.sh" --platform azure
python3 main.py --experiment_name "train_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o-mini.sh" --platform azure

# CoreAgent with GPT-4o (Cost Ablation)
python3 main.py --experiment_name "train_coreagent_gpt4o_c-10" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o_cost_10.sh" --platform azure

# CoreAgent with GPT-4o-mini (Cost Ablation)
python3 main.py --experiment_name "train_coreagent_gpt4o-mini_c-10" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_train.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o-mini_cost_10.sh" --platform azure

# ------- Experiments on Test Set -------
# AutoGPT with GPT-4o
python3 main.py --experiment_name "test_autogpt_gpt4o_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --platform azure
python3 main.py --experiment_name "test_autogpt_gpt4o_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --platform azure
python3 main.py --experiment_name "test_autogpt_gpt4o_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o.sh" --platform azure

# AutoGPT with GPT-4o-mini
python3 main.py --experiment_name "test_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --platform azure
python3 main.py --experiment_name "test_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --platform azure
python3 main.py --experiment_name "test_autogpt_gpt4o-mini_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "autogpt_gpt4o-mini.sh" --platform azure

# CORE-Agent with GPT-4o
python3 main.py --experiment_name "test_coreagent_gpt4o_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_easy_gpt4o.sh" --platform azure
python3 main.py --experiment_name "test_coreagent_gpt4o_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_medium_gpt4o.sh" --platform azure
python3 main.py --experiment_name "test_coreagent_gpt4o_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o.sh" --platform azure

# CORE-Agent with GPT-4o-mini
python3 main.py --experiment_name "test_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_easy" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_easy_gpt4o-mini.sh" --platform azure
python3 main.py --experiment_name "test_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_medium" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_medium_gpt4o-mini.sh" --platform azure
python3 main.py --experiment_name "test_coreagent_gpt4o-mini_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_gpt4o-mini.sh" --platform azure

# ------- Experiments on Test Set (not included in paper) -------
# CORE-Agent with o1-mini
python3 main.py --experiment_name "test_coreagent_o1-mini_c-10" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_o1-mini_cost_10.sh" --platform azure --resume benchmark/results/test_coreagent_o1-mini_c-10/20241013-200729_codeocean_hard.json

# CORE-Agent with Claude-3-5-Sonnet
python main.py --experiment_name "test_coreagent_claude_35_sonnet_c-4" --benchmark_level "codeocean_hard" --dataset_file "benchmark/dataset/core_test.json" --agent_dir "agents/AutoGPT-CORE" --agent_script "coreagent_hard_claude_35_sonnet.sh" --platform azure