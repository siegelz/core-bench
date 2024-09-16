import logging

from colorama import Fore, Style
from google.cloud.logging_v2.handlers import CloudLoggingFilter, StructuredLogHandler

from .utils import remove_color_codes
import json


class FancyConsoleFormatter(logging.Formatter):
    """
    A custom logging formatter designed for console output.

    This formatter enhances the standard logging output with color coding. The color
    coding is based on the level of the log message, making it easier to distinguish
    between different types of messages in the console output.

    The color for each level is defined in the LEVEL_COLOR_MAP class attribute.
    """

    # level -> (level & text color, title color)
    LEVEL_COLOR_MAP = {
        logging.DEBUG: Fore.LIGHTBLACK_EX,
        logging.INFO: Fore.BLUE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        # Create a log record dictionary
        log_record = {
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        
        # Add any additional attributes you want in the log record
        if hasattr(record, 'input_messages'):
            log_record['input_messages'] = record.input_messages
        # Add any additional attributes you want in the log record
        if hasattr(record, 'output_messages'):
            log_record['output_messages'] = record.output_messages
        if hasattr(record, 'task_time'):
            log_record['task_time'] = record.task_time
        if hasattr(record, 'inference_time'):
            log_record['inference_time'] = record.inference_time
        if hasattr(record, 'task_id'):
            log_record['task_id'] = record.task_id
        if hasattr(record, 'accuracy'):
            log_record['accuracy'] = record.accuracy
        if hasattr(record, 'run_parameters'):
            log_record['run_parameters'] = record.run_parameters
        if hasattr(record, 'task_id'):
            log_record['task_id'] = record.task_id
        if hasattr(record, 'model_name'):
            log_record['model_name'] = record.model_name
        if hasattr(record, "prompt_tokens"):
            log_record["prompt_tokens"] = record.prompt_tokens
        if hasattr(record, "prompt_tokens"):
            log_record["prompt_tokens"] = record.prompt_tokens
        if hasattr(record, "completion_tokens"):
            log_record["completion_tokens"] = record.completion_tokens
        if hasattr(record, "total_tokens"):
            log_record["total_tokens"] = record.total_tokens
        if hasattr(record, "type"):
            log_record["type"] = record.type
        if hasattr(record, "task_is_solved"):
            log_record["task_is_solved"] = record.task_is_solved
        if hasattr(record, "boosting_steps"):
            log_record["boosting_steps"] = record.boosting_steps
        if hasattr(record, "new_model_name"):
            log_record["new_model_name"] = record.new_model_name
        if hasattr(record, "temperature"):
            log_record["temperature"] = record.temperature
        if hasattr(record, "embedding_tokens"):
            log_record["embedding_tokens"] = record.embedding_tokens

        # Make sure `msg` is a string
        if not hasattr(record, "msg"):
            record.msg = ""
        elif not type(record.msg) is str:
            record.msg = str(record.msg)

        # append the log record to the message
        if hasattr(record, "type") and record.type == "api_call":
            record.msg = f"\n{json.dumps(log_record)}"

        # Determine default color based on error level
        level_color = ""
        if record.levelno in self.LEVEL_COLOR_MAP:
            level_color = self.LEVEL_COLOR_MAP[record.levelno]
            record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"

        # Determine color for message
        color = getattr(record, "color", level_color)
        color_is_specified = hasattr(record, "color")

        # Don't color INFO messages unless the color is explicitly specified.
        if color and (record.levelno != logging.INFO or color_is_specified):
            record.msg = f"{color}{record.msg}{Style.RESET_ALL}"

        return super().format(record)


class ForgeFormatter(FancyConsoleFormatter):
    def __init__(self, *args, no_color: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.no_color = no_color

    def format(self, record: logging.LogRecord) -> str:
        # Create a log record dictionary
        log_record = {
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        
        # Add any additional attributes you want in the log record
        if hasattr(record, 'input_messages'):
            log_record['input_messages'] = record.input_messages
        # Add any additional attributes you want in the log record
        if hasattr(record, 'output_messages'):
            log_record['output_messages'] = record.output_messages
        if hasattr(record, 'task_time'):
            log_record['task_time'] = record.task_time
        if hasattr(record, 'inference_time'):
            log_record['inference_time'] = record.inference_time
        if hasattr(record, 'task_id'):
            log_record['task_id'] = record.task_id
        if hasattr(record, 'accuracy'):
            log_record['accuracy'] = record.accuracy
        if hasattr(record, 'run_parameters'):
            log_record['run_parameters'] = record.run_parameters
        if hasattr(record, 'task_id'):
            log_record['task_id'] = record.task_id
        if hasattr(record, 'model_name'):
            log_record['model_name'] = record.model_name
        if hasattr(record, "prompt_tokens"):
            log_record["prompt_tokens"] = record.prompt_tokens
        if hasattr(record, "prompt_tokens"):
            log_record["prompt_tokens"] = record.prompt_tokens
        if hasattr(record, "completion_tokens"):
            log_record["completion_tokens"] = record.completion_tokens
        if hasattr(record, "total_tokens"):
            log_record["total_tokens"] = record.total_tokens
        if hasattr(record, "type"):
            log_record["type"] = record.type
        if hasattr(record, "task_is_solved"):
            log_record["task_is_solved"] = record.task_is_solved
        if hasattr(record, "boosting_steps"):
            log_record["boosting_steps"] = record.boosting_steps
        if hasattr(record, "new_model_name"):
            log_record["new_model_name"] = record.new_model_name
        if hasattr(record, "temperature"):
            log_record["temperature"] = record.temperature
        if hasattr(record, "embedding_tokens"):
            log_record["embedding_tokens"] = record.embedding_tokens
        json.dumps(log_record)

        # Make sure `msg` is a string
        if not hasattr(record, "msg"):
            record.msg = ""
        elif not type(record.msg) is str:
            record.msg = str(record.msg)

        # append the log record to the message
        if hasattr(record, "type") and record.type == "api_call":
            record.msg = f"\n{json.dumps(log_record)}"

        # Strip color from the message to prevent color spoofing
        if record.msg and not getattr(record, "preserve_color", False):
            record.msg = remove_color_codes(record.msg)

        # Determine color for title
        title = getattr(record, "title", "")
        title_color = getattr(record, "title_color", "") or self.LEVEL_COLOR_MAP.get(
            record.levelno, ""
        )
        if title and title_color:
            title = f"{title_color + Style.BRIGHT}{title}{Style.RESET_ALL}"
        # Make sure record.title is set, and padded with a space if not empty
        record.title = f"{title} " if title else ""

        if self.no_color:
            return remove_color_codes(super().format(record))
        else:
            return super().format(record)


class StructuredLoggingFormatter(StructuredLogHandler, logging.Formatter):
    def __init__(self):
        # Set up CloudLoggingFilter to add diagnostic info to the log records
        self.cloud_logging_filter = CloudLoggingFilter()

        # Init StructuredLogHandler
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        # Create a log record dictionary
        log_record = {
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        
        # Add any additional attributes you want in the log record
        if hasattr(record, 'input_messages'):
            log_record['input_messages'] = record.input_messages
        # Add any additional attributes you want in the log record
        if hasattr(record, 'output_messages'):
            log_record['output_messages'] = record.output_messages
        if hasattr(record, 'task_time'):
            log_record['task_time'] = record.task_time
        if hasattr(record, 'inference_time'):
            log_record['inference_time'] = record.inference_time
        if hasattr(record, 'task_id'):
            log_record['task_id'] = record.task_id
        if hasattr(record, 'accuracy'):
            log_record['accuracy'] = record.accuracy
        if hasattr(record, 'run_parameters'):
            log_record['run_parameters'] = record.run_parameters
        if hasattr(record, 'task_id'):
            log_record['task_id'] = record.task_id
        if hasattr(record, 'model_name'):
            log_record['model_name'] = record.model_name
        if hasattr(record, "prompt_tokens"):
            log_record["prompt_tokens"] = record.prompt_tokens
        if hasattr(record, "prompt_tokens"):
            log_record["prompt_tokens"] = record.prompt_tokens
        if hasattr(record, "completion_tokens"):
            log_record["completion_tokens"] = record.completion_tokens
        if hasattr(record, "total_tokens"):
            log_record["total_tokens"] = record.total_tokens
        if hasattr(record, "type"):
            log_record["type"] = record.type
        if hasattr(record, "task_is_solved"):
            log_record["task_is_solved"] = record.task_is_solved
        if hasattr(record, "boosting_steps"):
            log_record["boosting_steps"] = record.boosting_steps
        if hasattr(record, "new_model_name"):
            log_record["new_model_name"] = record.new_model_name
        if hasattr(record, "temperature"):
            log_record["temperature"] = record.temperature
        if hasattr(record, "embedding_tokens"):
            log_record["embedding_tokens"] = record.embedding_tokens
        json.dumps(log_record)


        # append the log record to the message
        if hasattr(record, "type") and record.type == "api_call":
            record.msg = f"\n{json.dumps(log_record)}"

        self.cloud_logging_filter.filter(record)
        return super().format(record)
