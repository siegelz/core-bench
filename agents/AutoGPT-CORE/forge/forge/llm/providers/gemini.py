from __future__ import annotations

import enum
import logging
from typing import TYPE_CHECKING, Any, Callable, Optional, ParamSpec, Sequence, TypeVar

import sentry_sdk
import tenacity
from pydantic.v1 import SecretStr
import tiktoken

from forge.models.config import UserConfigurable

from .schema import (
    AssistantChatMessage,
    AssistantFunctionCall,
    AssistantToolCall,
    BaseChatModelProvider,
    ChatMessage,
    ChatModelInfo,
    ChatModelResponse,
    CompletionModelFunction,
    ModelProviderBudget,
    ModelProviderConfiguration,
    ModelProviderCredentials,
    ModelProviderName,
    ModelProviderSettings,
    ModelTokenizer,
    ToolResultMessage,
)
from .utils import validate_tool_calls

if TYPE_CHECKING:
    import google.generativeai as genai

_T = TypeVar("_T")
_P = ParamSpec("_P")


class GeminiModelName(str, enum.Enum):
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"

GEMINI_CHAT_MODELS = {
    info.name: info
    for info in [
        ChatModelInfo(
            name=GeminiModelName.GEMINI_1_5_FLASH,
            provider_name=ModelProviderName.GEMINI,
            prompt_token_cost=0.00025 / 1000,  # Placeholder values, update when available
            completion_token_cost=0.0005 / 1000,
            max_tokens=32000,
            has_function_call_api=True,
        ),
        ChatModelInfo(
            name=GeminiModelName.GEMINI_1_5_PRO,
            provider_name=ModelProviderName.GEMINI,
            prompt_token_cost=0.0005 / 1000,  # Placeholder values, update when available
            completion_token_cost=0.001 / 1000,
            max_tokens=32000,
            has_function_call_api=True,
        )
    ]
}


class GeminiCredentials(ModelProviderCredentials):
    """Credentials for Gemini."""

    api_key: SecretStr = UserConfigurable(from_env="GEMINI_API_KEY")  # type: ignore

    def get_api_access_kwargs(self) -> dict[str, str]:
        return {"api_key": self.api_key.get_secret_value()}


class GeminiSettings(ModelProviderSettings):
    credentials: Optional[GeminiCredentials]  # type: ignore
    budget: ModelProviderBudget  # type: ignore


class GeminiProvider(BaseChatModelProvider[GeminiModelName, GeminiSettings]):
    default_settings = GeminiSettings(
        name="gemini_provider",
        description="Provides access to Google's Gemini API.",
        configuration=ModelProviderConfiguration(),
        credentials=None,
        budget=ModelProviderBudget(),
    )

    _settings: GeminiSettings
    _credentials: GeminiCredentials
    _budget: ModelProviderBudget

    def __init__(
        self,
        settings: Optional[GeminiSettings] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if not settings:
            settings = self.default_settings.copy(deep=True)
        if not settings.credentials:
            settings.credentials = GeminiCredentials.from_env()

        super(GeminiProvider, self).__init__(settings=settings, logger=logger)

        import google.generativeai as genai

        genai.configure(**self._credentials.get_api_access_kwargs())
        self._client = genai

    async def get_available_models(self) -> Sequence[ChatModelInfo[GeminiModelName]]:
        return await self.get_available_chat_models()

    async def get_available_chat_models(
        self,
    ) -> Sequence[ChatModelInfo[GeminiModelName]]:
        return list(GEMINI_CHAT_MODELS.values())

    def get_token_limit(self, model_name: GeminiModelName) -> int:
        """Get the token limit for a given model."""
        return GEMINI_CHAT_MODELS[model_name].max_tokens

    def count_tokens(self, text: str, model: genai.GenerativeModel) -> int:
        return model.count_tokens(text)

    def count_message_tokens(
        self,
        messages: ChatMessage | list[ChatMessage],
        model: genai.GenerativeModel,
    ) -> int:
        return model.count_tokens(messages)

    async def create_chat_completion(
        self,
        model_prompt: list[ChatMessage],
        model_name: GeminiModelName,
        completion_parser: Callable[[AssistantChatMessage], _T] = lambda _: None,
        functions: Optional[list[CompletionModelFunction]] = None,
        max_output_tokens: Optional[int] = None,
        prefill_response: str = "",
        **kwargs,
    ) -> ChatModelResponse[_T]:
        """Create a completion using the Gemini API."""
        gemini_messages, completion_kwargs = self._get_chat_completion_args(
            prompt_messages=model_prompt,
            model=model_name,
            functions=functions,
            max_output_tokens=max_output_tokens,
            **kwargs,
        )

        while True:
            completion_kwargs["contents"] = gemini_messages.copy()
            if prefill_response:
                completion_kwargs["contents"].append(
                    {"role": "model", "parts": [{"text": prefill_response}]}
                )

            (
                _assistant_msg,
                t_input,
                t_output,
            ) = await self._create_chat_completion(model_name, completion_kwargs)

            # Merge prefill into generated response
            if prefill_response:
                _assistant_msg.text = prefill_response + _assistant_msg.text

            assistant_msg = AssistantChatMessage(
                content=_assistant_msg.text,
            )

            try:
                parsed_result = completion_parser(assistant_msg)
                break
            except Exception as e:
                self._logger.debug(
                    f"Parsing failed on response: '''{_assistant_msg}'''"
                )

        return ChatModelResponse(
            response=assistant_msg,
            parsed_result=parsed_result,
            model_info=GEMINI_CHAT_MODELS[model_name],
            prompt_tokens_used=t_input,
            completion_tokens_used=t_output,
        )

    def _get_chat_completion_args(
        self,
        prompt_messages: list[ChatMessage],
        functions: Optional[list[CompletionModelFunction]] = None,
        max_output_tokens: Optional[int] = None,
        **kwargs,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Prepare arguments for message completion API call."""
        if functions:
            pass

        kwargs["max_output_tokens"] = max_output_tokens or 1024

        messages: list[dict[str, Any]] = []
        for message in prompt_messages:
            if message.role == ChatMessage.Role.SYSTEM:
                messages.append({"role": "user", "parts": [{"text": message.content}]})
            elif message.role == ChatMessage.Role.USER:
                messages.append({"role": "user", "parts": [{"text": message.content}]})
            elif message.role == ChatMessage.Role.ASSISTANT:
                messages.append({"role": "model", "parts": [{"text": message.content}]})
            else:
                raise ValueError(f"Invalid message role: {message.role}")

        return messages, kwargs

    async def _create_chat_completion(
        self, model: GeminiModelName, completion_kwargs: dict[str, Any]
    ) -> tuple[genai.types.GenerateContentResponse, float, int, int]:
        """Create a chat completion using the Gemini API with retry handling."""

        @self._retry_api_request
        async def _create_chat_completion_with_retry():
            gemini_model = self._client.GenerativeModel(model.value)
            chat = gemini_model.start_chat(history=completion_kwargs["contents"][:-1])
            return await chat.send_message_async(completion_kwargs["contents"][-1]["parts"][0]["text"])

        response = await _create_chat_completion_with_retry()

        input_tokens = self.count_message_tokens(completion_kwargs["contents"], self._client.GenerativeModel(model.value))
        output_tokens = self.count_tokens(response.text, self._client.GenerativeModel(model.value))

        return response, input_tokens, output_tokens


    def _retry_api_request(self, func: Callable[_P, _T]) -> Callable[_P, _T]:
        return tenacity.retry(
            retry=tenacity.retry_if_exception_type(Exception),  # Adjust exception types as needed
            wait=tenacity.wait_exponential(),
            stop=tenacity.stop_after_attempt(self._configuration.retries_per_request),
            after=tenacity.after_log(self._logger, logging.DEBUG),
        )(func)

    def __repr__(self):
        return "GeminiProvider()"