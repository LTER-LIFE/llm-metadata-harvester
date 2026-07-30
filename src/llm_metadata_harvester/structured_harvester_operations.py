"""Structured-output variant of the metadata harvester pipeline."""

from __future__ import annotations

from typing import Any

from llm_metadata_harvester.checks import check_exist, check_repeat_prompt
from llm_metadata_harvester.harvester_operations import chunk_text
from llm_metadata_harvester.llm_client import LLMClient
from llm_metadata_harvester.standards import LTER_LIFE_STANDARD, filter_metadata_standard
from llm_metadata_harvester.structured_schemas import (
    coerce_metadata_result,
    metadata_model_to_json_schema,
    metadata_standard_to_model,
)
from llm_metadata_harvester.utils import dump_meta_to_json, logger
from llm_metadata_harvester.webutils import extract_full_page_text

_METADATA_SYSTEM_PROMPT = (
    "You extract dataset metadata from text. "
    "Return only the requested fields as a JSON object. "
    "Use null when a value is not present in the text."
)


def _build_extraction_prompt(
    metadata_standard: dict[str, str],
    input_text: str,
    language: str = "English",
) -> str:
    lines = [
        f"Extract metadata from the text below. Use {language} for values when possible.",
        "Return one concise value per field. Use null when the information is not in the text.",
        "",
        "Fields:",
    ]
    for field_name, description in metadata_standard.items():
        lines.append(f"- {field_name}: {description}")
    lines.extend(["", "Text:", input_text])
    return "\n".join(lines)


def _llm_call(
    llm: LLMClient,
    messages: list[dict],
    schema_name: str,
    schema: dict,
    max_tokens: int,
) -> dict:
    return llm.chat_structured(
        messages,
        schema_name=schema_name,
        schema=schema,
        max_tokens=max_tokens,
    )


def _merge_metadata_dicts(
    base: dict[str, Any],
    update: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(base)
    for field_name, value in update.items():
        if value is None:
            continue
        text = str(value).strip()
        if not text or text.lower() == "n/a":
            continue
        if merged.get(field_name) in (None, ""):
            merged[field_name] = text
    return merged


def extract_metadata_structured(
    text: str,
    metadata_standard: dict[str, str],
    llm: LLMClient,
    language: str = "English",
) -> dict[str, str | None]:
    """Extract metadata fields directly via one structured LLM call per text chunk."""
    model = metadata_standard_to_model(metadata_standard)
    schema = metadata_model_to_json_schema(model)
    chunks = chunk_text(text, llm, max_tokens=llm.get_chunk_token_limit())

    merged: dict[str, Any] = {field_name: None for field_name in metadata_standard}

    for chunk in chunks:
        messages = [
            {"role": "system", "content": _METADATA_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_extraction_prompt(
                    metadata_standard,
                    chunk,
                    language=language,
                ),
            },
        ]
        result = _llm_call(
            llm,
            messages,
            schema_name="metadata_extraction",
            schema=schema,
            max_tokens=llm.structured_max_output_tokens,
        )
        result = coerce_metadata_result(result, metadata_standard)
        validated = model.model_validate(result)
        merged = _merge_metadata_dicts(merged, validated.model_dump())

    return merged


async def metadata_harvest_structured(
    model_name: str,
    url: str,
    api_key: str = None,
    metadata_standard: dict = LTER_LIFE_STANDARD,
    fields: list[str] | None = None,
    dump_format: str = "none",
    allow_retrying: bool = False,
) -> dict:
    if dump_format not in ["json", "yaml", "none"]:
        raise ValueError("dump_format must be one of 'json', 'yaml', or 'none'")
    metadata_standard = filter_metadata_standard(metadata_standard, fields)

    print("Extracting full page text...")
    full_text = await extract_full_page_text(url)
    llm = LLMClient(model_name=model_name, temperature=0.0, api_key=api_key)

    print("Extracting metadata (structured output)...")
    metadata = extract_metadata_structured(
        text=full_text,
        metadata_standard=metadata_standard,
        llm=llm,
    )

    if allow_retrying:
        for attempt in range(3):
            print(f"Retry attempt {attempt + 1} for missing fields...")
            check_exist_results = check_exist(
                extracted_metadata=metadata,
                raw_input=full_text,
                threshold=0.8,
            )
            check_repeat_results = check_repeat_prompt(
                extracted_metadata=metadata,
                metadata_definition=metadata_standard,
                threshold=0.8,
            )
            missing_fields = [
                field
                for field in metadata_standard
                if (
                    check_exist_results.get(field) is False
                    or check_repeat_results.get(field) is True
                )
            ]

            if not missing_fields:
                break

            logger.info(f"Retrying extraction for missing fields: {missing_fields}")
            refined_standard = {
                field: metadata_standard[field] for field in missing_fields
            }
            refined_metadata = extract_metadata_structured(
                text=full_text,
                metadata_standard=refined_standard,
                llm=llm,
            )
            metadata = _merge_metadata_dicts(metadata, refined_metadata)

    if dump_format == "json":
        dump_meta_to_json("extracted_metadata.json", metadata)
    elif dump_format == "yaml":
        dump_meta_to_json("extracted_metadata.yaml", metadata, as_yaml=True)

    return metadata
