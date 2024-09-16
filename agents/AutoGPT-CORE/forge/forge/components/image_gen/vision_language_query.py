"""Commands to query a vision langauge model with image and text input"""

import io
import os
import json
import logging
import time
import uuid
from base64 import b64decode
from pathlib import Path
from typing import Iterator
import base64

import requests
from openai import OpenAI
from PIL import Image

from forge.agent.protocols import CommandProvider
from forge.command import Command, command
from forge.config.config import Config
from forge.config.config import GPT_4_O_MODEL
from forge.models.config import UserConfigurable
from forge.file_storage import FileStorage
from forge.models.json_schema import JSONSchema

logger = logging.getLogger(__name__)

class VisionLanguageQueryComponent(CommandProvider):
    """Component to query a vision language model with image and text input."""

    def __init__(self, workspace: FileStorage, config: Config):
        self.workspace = workspace
        self.legacy_config = config
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def get_commands(self) -> Iterator[Command]:
        if self.legacy_config.openai_credentials:
            yield self.query_vision_language_model

    @command(
        parameters={
            "prompt": JSONSchema(
                type=JSONSchema.Type.STRING,
                description="The prompt used to query the vision language model with alongside the image input",
                required=True,
            ),
            "input_image_paths": JSONSchema(
                type=JSONSchema.Type.ARRAY,
                description="An array of image paths to use as input to the vision language model.",
                required=True,
            ),
        },
    )
    def query_vision_language_model(self, prompt: str, input_image_paths: list) -> str:
        """Query a vision language model with an image and text input.

        Args:
            prompt (str): The prompt to use
            input_image_paths (str): The path to the input image

        Returns:
            str: The response from the vision language model
        """
        cfg = self.legacy_config

        if cfg.openai_credentials:
            return self.openai_query(prompt, input_image_paths)

        return "Error: No vlm provider available"


    def encode_image(self, image_path):
        """Encodes an image as a base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def openai_query(
        self, prompt: str, input_image_paths: list
    ) -> str:
        assert self.legacy_config.openai_credentials  # otherwise this tool is disabled

        base64_images = []
        for input_image_path in input_image_paths:
            image_path = self.workspace.root / input_image_path

            # Upload the image to the workspace
            base64_image = self.encode_image(image_path)
            base64_images.append(base64_image)

        start_time = time.time()

        # Construct the message with multiple images
        message_content = [{"type": "text", "text": prompt}]
        for base64_image in base64_images:
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })

        # Payload for OpenAI API
        payload = {
            "model": os.getenv("VLM_MODEL", "gpt-4"),
            "messages": [
                {
                    "role": "user",
                    "content": message_content
                }
            ],
        }

        # Make a request to OpenAI API
        response = self.client.chat.completions.create(**payload)

        end_time = time.time()
        logger.info("OpenAI API VLM call", extra={
            "input_messages": prompt,
            "output_messages": response.choices[0].message.content,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "inference_time": end_time - start_time,
            "model_name": response.model,
            "type": "api_call",
        })

        return response.choices[0].message.content

