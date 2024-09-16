import logging
import time
from typing import Iterator
import os
import json
import re
import ast
from pathlib import Path


from forge.agent.protocols import CommandProvider, DirectiveProvider, MessageProvider
from forge.command import Command, command
from forge.llm.providers import ChatMessage
from forge.models.json_schema import JSONSchema
from forge.utils.const import FINISH_COMMAND
from forge.utils.exceptions import AgentFinished
from forge.file_storage import FileStorage

logger = logging.getLogger(__name__)


class SystemComponent(DirectiveProvider, MessageProvider, CommandProvider):
    """Component for system messages and commands."""

    def __init__(self, workspace: FileStorage):
        self.workspace = workspace

    def get_constraints(self) -> Iterator[str]:
        yield "Exclusively use the commands listed below."
        yield (
            "You can only act proactively, and are unable to start background jobs or "
            "set up webhooks for yourself. "
            "Take this into account when planning your actions."
        )
        yield (
            "You are unable to interact with physical objects. "
            "If this is absolutely necessary to fulfill a task or objective or "
            "to complete a step, you must ask the user to do it for you. "
            "If the user refuses this, and there is no other way to achieve your "
            "goals, you must terminate to avoid wasting time and energy."
        )

    def get_resources(self) -> Iterator[str]:
        yield (
            "You are a Large Language Model, trained on millions of pages of text, "
            "including a lot of factual knowledge. Make use of this factual knowledge "
            "to avoid unnecessary gathering of information."
        )

    def get_best_practices(self) -> Iterator[str]:
        yield (
            "Continuously review and analyze your actions to ensure "
            "you are performing to the best of your abilities."
        )
        yield "Constructively self-criticize your big-picture behavior constantly."
        yield "Reflect on past decisions and strategies to refine your approach."
        yield (
            "Every command has a cost, so be smart and efficient. "
            "Aim to complete tasks in the least number of steps."
        )
        yield (
            "Only make use of your information gathering abilities to find "
            "information that you don't yet have knowledge of."
        )

    def get_messages(self) -> Iterator[ChatMessage]:
        # Clock
        yield ChatMessage.system(
            f"## Clock\nThe current time and date is {time.strftime('%c')}"
        )

    def get_commands(self) -> Iterator[Command]:
        yield self.finish

    @command(
        names=[FINISH_COMMAND],
        parameters={
            "reason": JSONSchema(
                type=JSONSchema.Type.STRING,
                description="A summary to the user of how the goals were accomplished",
                required=True,
            ),
        },
    )
    def finish(self, reason: str):
        """Use this to shut down once you have completed your task,
        or when there are insurmountable problems that make it impossible
        for you to finish your task."""

        if os.getenv("PROGRAMMATIC_KEY_CHECK", "False").lower() == "true":
            print("PROGRAMMATIC_KEY_CHECK executing")
            report_json_path = self.workspace.root / "report.json"
            # Check if the report.json file exists
            if not os.path.exists(report_json_path):
                return f"You have indicated that the task is complete. However, I do not see a 'report.json' file in the directory. The correct filepath is: {self.workspace.root}. Here are the files currently there: {os.listdir(self.workspace.root)}. Please write the results to 'report.json' before finishing."
            # Check that the keys in the report.json file are correct
            task_txt_path = str(os.path.abspath(__file__)).replace("forge/forge/components/system/system.py", "autogpt/environment/task.txt")
            correct_keys = self.get_json_keys(task_txt_path)
            try:
                result_keys = json.load(open(Path(report_json_path), "r")).keys()
                if set(correct_keys) != set(result_keys):
                    os.remove(report_json_path)
                    return f"You have indicated that the task is complete. However, the keys in the 'report.json' file do not match the keys in the task specified by the user. The correct keys are {correct_keys}. I have deleted the report.json file. Please re-create it, ensuring the keys are correct before finishing."
            except Exception as e:
                print("EXCEPTION", e)
                os.remove(report_json_path)
                return f"You have indicated that the task is complete. However, the keys in the 'report.json' file do not match the keys in the task specified by the user. The correct keys are {correct_keys}. I have deleted the report.json file. Please re-create it, ensuring the keys are correct before finishing."
            
        raise AgentFinished(reason)
    

    def get_json_keys(self, filepath):
        try:
            with open(filepath, "r") as f:
                task_str = f.read()
        except Exception:
            return []

        # Regular expression to find the dict_keys part
        pattern = r"dict_keys\((\[.*?\])\)"
        match = re.search(pattern, task_str)

        if match:
            list_str = match.group(1)
            array = ast.literal_eval(list_str)
            return array
        else:
            return []

    
        
