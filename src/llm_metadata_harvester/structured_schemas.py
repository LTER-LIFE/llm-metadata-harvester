"""Pydantic models and JSON schemas for structured metadata extraction."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, create_model


def metadata_standard_to_model(
    metadata_standard: dict[str, str],
    model_name: str = "ExtractedMetadata",
) -> type[BaseModel]:
    """Build a Pydantic model from a metadata standard field-definition dict."""
    field_definitions: dict[str, tuple] = {}
    for field_name, description in metadata_standard.items():
        field_definitions[field_name] = (
            Optional[str],
            Field(default=None, description=description),
        )
    return create_model(model_name, **field_definitions)


def metadata_model_to_json_schema(model: type[BaseModel]) -> dict:
    """Convert a metadata Pydantic model to a strict JSON schema for LLM APIs."""
    properties: dict[str, dict] = {}
    required: list[str] = []

    for field_name, field_info in model.model_fields.items():
        properties[field_name] = {
            "type": ["string", "null"],
            "description": field_info.description or "",
        }
        required.append(field_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def coerce_metadata_result(
    result: dict,
    metadata_standard: dict[str, str],
) -> dict[str, str | None]:
    """Normalize LLM JSON keys and values before Pydantic validation."""
    standard_by_lower = {name.lower(): name for name in metadata_standard}
    coerced: dict[str, str | None] = {}

    for field_name in metadata_standard:
        value = result.get(field_name)
        if value is None:
            for key, candidate in result.items():
                if key.lower() == field_name.lower():
                    value = candidate
                    break

        if value is None:
            coerced[field_name] = None
        elif isinstance(value, list):
            coerced[field_name] = ", ".join(str(item) for item in value)
        elif isinstance(value, str):
            coerced[field_name] = value
        else:
            coerced[field_name] = str(value)

    return coerced
