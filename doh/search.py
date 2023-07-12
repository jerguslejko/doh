from fuzzywuzzy import fuzz


def tags_similarity(needle: str, tag: str) -> int:
    return fuzz.partial_ratio(needle, tag)
