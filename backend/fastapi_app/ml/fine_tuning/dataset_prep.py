"""
CareerOS Dataset Preparation & Formatting Utilities
----------------------------------------------------
Provides utilities to format raw samples into ChatML format,
validate tokens, and prepare Hugging Face Dataset objects for Qwen fine-tuning.
"""

import json
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are CareerOS, an expert AI career co-pilot specializing in resume optimization, "
    "ATS keyword alignment, technical interview preparation, and ethical career guidance."
)


def format_instruction_sample(
    user_input: str,
    assistant_response: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
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


def load_jsonl_dataset(filepath: str) -> List[Dict[str, Any]]:
    """Loads a JSONL file into a list of dictionaries."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found at {filepath}")

    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON line {line_num} in {filepath}: {e}")
    return records


def prepare_dataset(
    raw_samples: List[Dict[str, str]],
    output_filepath: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
) -> int:
    """
    Processes a list of raw instruction dicts and writes JSONL dataset for Qwen training.
    """
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    count = 0

    with open(output_filepath, "w", encoding="utf-8") as f:
        for sample in raw_samples:
            user_content = sample.get("instruction", "")
            if sample.get("input", "").strip():
                user_content = f"{user_content}\n\n{sample['input']}"

            formatted = format_instruction_sample(
                system_prompt=sample.get("system", system_prompt),
                user_input=user_content,
                assistant_response=sample.get("output", "")
            )
            f.write(json.dumps(formatted, ensure_ascii=False) + "\n")
            count += 1

    logger.info(f"Prepared {count} training samples saved to {output_filepath}")
    return count
