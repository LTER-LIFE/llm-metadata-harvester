from llm_metadata_harvester.structured_schemas import (
    coerce_metadata_result,
    metadata_model_to_json_schema,
    metadata_standard_to_model,
)


def test_metadata_standard_to_model_creates_fields():
    standard = {
        "Title": "Dataset title",
        "Description": "Dataset description",
    }
    model = metadata_standard_to_model(standard, model_name="TestMetadata")

    instance = model.model_validate(
        {"Title": "My dataset", "Description": None}
    )
    assert instance.Title == "My dataset"
    assert instance.Description is None


def test_metadata_model_to_json_schema_matches_fields():
    standard = {"Title": "Dataset title"}
    model = metadata_standard_to_model(standard)
    schema = metadata_model_to_json_schema(model)

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert "Title" in schema["properties"]
    assert schema["properties"]["Title"]["description"] == "Dataset title"
    assert schema["required"] == ["Title"]


def test_coerce_metadata_result_joins_lists_and_matches_case():
    standard = {
        "Title": "Dataset title",
        "Keywords": "Dataset keywords",
    }
    result = {
        "title": "My dataset",
        "Keywords": ["a", "b", "c"],
    }

    coerced = coerce_metadata_result(result, standard)

    assert coerced == {
        "Title": "My dataset",
        "Keywords": "a, b, c",
    }
