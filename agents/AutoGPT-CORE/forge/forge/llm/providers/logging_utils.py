import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
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

        
        return json.dumps(log_record)
