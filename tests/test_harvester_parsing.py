from llm_metadata_harvester.harvester_operations import (
    _handle_post_processed_entity_extraction,
)


def test_handle_post_processed_entity_extraction_accepts_entity_prefix():
    record_attributes = ['"entity"', '"Title"', '"SIBES dataset"']

    parsed = _handle_post_processed_entity_extraction(
        record_attributes,
        chunk_key="chunk_0",
    )

    assert parsed == {
        "entity_name": "Title",
        "entity_value": "SIBES dataset",
        "source_id": "chunk_0",
        "file_path": "unknown_source",
    }


def test_handle_post_processed_entity_extraction_accepts_qwen_style_output():
    record_attributes = ['"Title"', "Title", "SIBES dataset"]

    parsed = _handle_post_processed_entity_extraction(
        record_attributes,
        chunk_key="chunk_0",
    )

    assert parsed == {
        "entity_name": "Title",
        "entity_value": "SIBES dataset",
        "source_id": "chunk_0",
        "file_path": "unknown_source",
    }
