import pytest

from llm_metadata_harvester.standards import filter_metadata_standard


def test_filter_metadata_standard_returns_full_standard_when_fields_is_none():
    standard = {"Title": "Dataset title", "Description": "Dataset description"}

    assert filter_metadata_standard(standard) == standard


def test_filter_metadata_standard_returns_requested_subset():
    standard = {
        "Title": "Dataset title",
        "Description": "Dataset description",
        "Keywords": "Dataset keywords",
    }

    filtered = filter_metadata_standard(standard, ["Keywords", "Title"])

    assert filtered == {
        "Keywords": "Dataset keywords",
        "Title": "Dataset title",
    }


def test_filter_metadata_standard_raises_for_unknown_fields():
    standard = {"Title": "Dataset title"}

    with pytest.raises(ValueError, match="Unknown metadata field"):
        filter_metadata_standard(standard, ["Title", "Missing field"])
