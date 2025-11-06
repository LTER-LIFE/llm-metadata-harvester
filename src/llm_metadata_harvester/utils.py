from __future__ import annotations

import asyncio
import html
import io
import csv
import json
import logging
import logging.handlers
import os
import re
import yaml
from dataclasses import dataclass
from functools import wraps
from hashlib import md5
from typing import Any, Callable, TYPE_CHECKING, Union, List, Dict, Optional
import xml.etree.ElementTree as ET
from llm_metadata_harvester.prompt import PROMPTS
from dotenv import load_dotenv

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from lightrag.base import BaseKVStorage

# use the .env that is inside the current folder
# allows to use different .env file for each lightrag instance
# the OS environment variables take precedence over the .env file
load_dotenv(dotenv_path=".env", override=False)

VERBOSE_DEBUG = os.getenv("VERBOSE", "false").lower() == "true"


statistic_data = {"llm_call": 0, "llm_cache": 0, "embed_call": 0}

# Initialize logger
logger = logging.getLogger("lightrag")
logger.propagate = False  # prevent log message send to root loggger
# Let the main application configure the handlers
logger.setLevel(logging.INFO)

# Set httpx logging level to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)


def compute_mdhash_id(content: str, prefix: str = "") -> str:
    """
    Compute a unique ID for a given content string.

    The ID is a combination of the given prefix and the MD5 hash of the content string.
    """
    return prefix + md5(content.encode()).hexdigest()


def limit_async_func_call(max_size: int):
    """Add restriction of maximum concurrent async calls using asyncio.Semaphore"""

    def final_decro(func):
        sem = asyncio.Semaphore(max_size)

        @wraps(func)
        async def wait_func(*args, **kwargs):
            async with sem:
                result = await func(*args, **kwargs)
                return result

        return wait_func

    return final_decro


def split_string_by_multi_markers(content: str, markers: list[str]) -> list[str]:
    """Split a string by multiple markers"""
    if not markers:
        return [content]
    content = content if content is not None else ""
    results = re.split("|".join(re.escape(marker) for marker in markers), content)
    return [r.strip() for r in results if r.strip()]


# Refer the utils functions of the official GraphRAG implementation:
# https://github.com/microsoft/graphrag
def clean_str(input: Any) -> str:
    """Clean an input string by removing HTML escapes, control characters, and other unwanted characters."""
    # If we get non-string input, just give it back
    if not isinstance(input, str):
        return input

    result = html.unescape(input.strip())
    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)


def is_float_regex(value: str) -> bool:
    return bool(re.match(r"^[-+]?[0-9]*\.?[0-9]+$", value))


def truncate_list_by_token_size(
    list_data: list[Any], key: Callable[[Any], str], max_token_size: int
) -> list[int]:
    """Truncate a list of data by token size"""
    if max_token_size <= 0:
        return []
    tokens = 0
    for i, data in enumerate(list_data):
        tokens += len(encode_string_by_tiktoken(key(data)))
        if tokens > max_token_size:
            return list_data[:i]
    return list_data


async def use_llm_func_with_cache(
    input_text: str,
    use_llm_func: callable,
    llm_response_cache: "Optional[BaseKVStorage]" = None,
    max_tokens: int = None,
    history_messages: List[Dict[str, str]] = None,
    cache_type: str = "extract",
) -> str:
    """Call LLM function with cache support

    If cache is available and enabled (determined by handle_cache based on mode),
    retrieve result from cache; otherwise call LLM function and save result to cache.

    Args:
        input_text: Input text to send to LLM
        use_llm_func: LLM function to call
        llm_response_cache: Cache storage instance
        max_tokens: Maximum tokens for generation
        history_messages: History messages list
        cache_type: Type of cache

    Returns:
        LLM response text
    """
    if llm_response_cache:
        if history_messages:
            history = json.dumps(history_messages, ensure_ascii=False)
            _prompt = history + "\n" + input_text
        else:
            _prompt = input_text

        arg_hash = compute_args_hash(_prompt)
        cached_return, _1, _2, _3 = await handle_cache(
            llm_response_cache,
            arg_hash,
            _prompt,
            "default",
            cache_type=cache_type,
        )
        if cached_return:
            logger.debug(f"Found cache for {arg_hash}")
            statistic_data["llm_cache"] += 1
            return cached_return
        statistic_data["llm_call"] += 1

        # Call LLM
        kwargs = {}
        if history_messages:
            kwargs["history_messages"] = history_messages
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        res: str = await use_llm_func(input_text, **kwargs)

        if llm_response_cache.global_config.get("enable_llm_cache_for_entity_extract"):
            await save_to_cache(
                llm_response_cache,
                CacheData(
                    args_hash=arg_hash,
                    content=res,
                    prompt=_prompt,
                    cache_type=cache_type,
                ),
            )

        return res

    # When cache is disabled, directly call LLM
    kwargs = {}
    if history_messages:
        kwargs["history_messages"] = history_messages
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    logger.info(f"Call LLM function with query text lenght: {len(input_text)}")
    return await use_llm_func(input_text, **kwargs)


def get_content_summary(content: str, max_length: int = 250) -> str:
    """Get summary of document content

    Args:
        content: Original document content
        max_length: Maximum length of summary

    Returns:
        Truncated content with ellipsis if needed
    """
    content = content.strip()
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."


def normalize_extracted_info(name: str, is_entity=False) -> str:
    """Normalize entity/relation names and description with the following rules:
    1. Remove spaces between Chinese characters
    2. Remove spaces between Chinese characters and English letters/numbers
    3. Preserve spaces within English text and numbers
    4. Replace Chinese parentheses with English parentheses
    5. Replace Chinese dash with English dash

    Args:
        name: Entity name to normalize

    Returns:
        Normalized entity name
    """
    # Replace Chinese parentheses with English parentheses
    name = name.replace("（", "(").replace("）", ")")

    # Replace Chinese dash with English dash
    name = name.replace("—", "-").replace("－", "-")

    # Use regex to remove spaces between Chinese characters
    # Regex explanation:
    # (?<=[\u4e00-\u9fa5]): Positive lookbehind for Chinese character
    # \s+: One or more whitespace characters
    # (?=[\u4e00-\u9fa5]): Positive lookahead for Chinese character
    name = re.sub(r"(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])", "", name)

    # Remove spaces between Chinese and English/numbers
    name = re.sub(r"(?<=[\u4e00-\u9fa5])\s+(?=[a-zA-Z0-9])", "", name)
    name = re.sub(r"(?<=[a-zA-Z0-9])\s+(?=[\u4e00-\u9fa5])", "", name)

    # Remove English quotation marks from the beginning and end
    name = name.strip('"').strip("'")

    if is_entity:
        # remove Chinese quotes
        name = name.replace("“", "").replace("”", "").replace("‘", "").replace("’", "")
        # remove English queotes in and around chinese
        name = re.sub(r"['\"]+(?=[\u4e00-\u9fa5])", "", name)
        name = re.sub(r"(?<=[\u4e00-\u9fa5])['\"]+", "", name)

    return name


def clean_text(text: str) -> str:
    """Clean text by removing null bytes (0x00) and whitespace

    Args:
        text: Input text to clean

    Returns:
        Cleaned text
    """
    return text.strip().replace("\x00", "")
    
def read_meta_from_json(file_path: str) -> dict:
    pass

def node_2_metadata(clean_nodes: dict) -> dict:
    """Convert nodes to metadata format"""
    metadata = {}
    for node_key, node_value_list in clean_nodes.items():
        metadata_value = ""
        for node_value in node_value_list:
            metadata_value += node_value["entity_value"] + "; "
        metadata[node_key] = metadata_value.strip()

    return metadata

def dump_meta_to_json(file_path: str, meta: dict, as_yaml: bool = False):
    """
    Dump metadata to a JSON/YAML file, creating directories if necessary.
    """
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    if as_yaml:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(meta, f, allow_unicode=True, sort_keys=False)
        return
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=4)
        return