import json
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def format_instruction_sample(
    system_prompt: str,
    user_input: str,
    assistant_response: str
) -> Dict[str, Any]:
    """
    Formats a single training example into ChatML format compatible with Qwen fine-tuning pipelines.
    """
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": assistant_response},
        ]
    }


def prepare_dataset(
    raw_samples: List[Dict[str, str]],
    output_filepath: str
) -> int:
    """
    Processes a list of raw instruction dicts and writes JSONL dataset for Qwen training.
    """
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    count = 0

    with open(output_filepath, "w", encoding="utf-8") as f:
        for sample in raw_samples:
            formatted = format_instruction_sample(
                system_prompt=sample.get("system", "You are CareerOS, an expert AI career co-pilot."),
                user_input=sample.get("input", ""),
                assistant_response=sample.get("output", "")
            )
            f.write(json.dumps(formatted) + "\n")
            count += 1

    logger.info(f"Prepared {count} training samples saved to {output_filepath}")
    return count
