# rule base checks
from difflib import SequenceMatcher


def check_exist(extracted_metadata: dict, raw_input: str, threshold: float = 0.8) -> dict[str, bool]:
    """Check if metadata value exist in raw input using fuzzy matching.

    For each value in ``extracted_metadata`` this does a fuzzy substring match
    against ``raw_input``. Returns a tuple of booleans for each metadata value.
    """

    if not extracted_metadata:
        raise ValueError("extracted_metadata is empty")

    hay = (raw_input or "").lower()
    if not hay:
        raise ValueError("raw_input is empty")

    results: dict[str, bool] = dict()
    for key, value in extracted_metadata.items():
        if value is None:
            results[key] = False
            continue
        needle = str(value).strip().lower()
        if not needle:
            results[key] = False
            continue

        # fast exact substring check first
        if needle in hay:
            results[key] = True
            continue

        n = len(needle)
        if n == 0:
            results[key] = False
            continue

        # allow some variation in window length (±20%) to improve substring matching
        delta = max(1, n // 5)
        min_w = max(1, n - delta)
        max_w = min(len(hay), n + delta)

        best_ratio = 0.0
        target = threshold

        found = False
        # slide windows over the haystack and compute similarity
        for w in range(min_w, max_w + 1):
            for i in range(0, len(hay) - w + 1):
                sub = hay[i : i + w]
                r = SequenceMatcher(None, needle, sub).ratio()
                if r > best_ratio:
                    best_ratio = r
                    if best_ratio >= target:
                        found = True
                        break
            if found:
                break
        results[key] = found

    return results


def check_repeat_prompt(extracted_metadata: dict, metadata_definition: dict, threshold: float = 0.8) -> dict[str, bool]:
    """Check if the metadata values are repeating the prompt."""
    if not extracted_metadata:
        raise ValueError("extracted_metadata is empty")

    if not metadata_definition:
        raise ValueError("metadata_definition is empty")

    results: dict[str, bool] = dict()
    for key, value in extracted_metadata.items():
        if key not in metadata_definition:
            raise ValueError(f"Key '{key}' not found in metadata_definition")
        
        metadata_definition_value = metadata_definition[key]
        hay = (metadata_definition_value or "").lower()
        if not hay:
            raise ValueError("metadata_definition value is empty")
        
        if value is None:
            results[key] = False
            continue
        needle = str(value).strip().lower()
        if not needle:
            results[key] = False
            continue

        # fast exact substring check first
        if needle in hay:
            results[key] = True
            continue

        n = len(needle)
        if n == 0:
            results[key] = False
            continue

        # allow some variation in window length (±20%) to improve substring matching
        delta = max(1, n // 5)
        min_w = max(1, n - delta)
        max_w = min(len(hay), n + delta)

        best_ratio = 0.0
        target = threshold

        found = False
        # slide windows over the haystack and compute similarity
        for w in range(min_w, max_w + 1):
            for i in range(0, len(hay) - w + 1):
                sub = hay[i : i + w]
                r = SequenceMatcher(None, needle, sub).ratio()
                if r > best_ratio:
                    best_ratio = r
                    if best_ratio >= target:
                        found = True
                        break
            if found:
                break
        results[key] = found
    return results