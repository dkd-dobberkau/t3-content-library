import os
import yaml


def load_page_structure(filepath: str) -> dict:
    """Load a single page structure definition from a YAML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_structures(directory: str) -> list[dict]:
    """Load all page structure YAML files from a directory, sorted by filename."""
    structures = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            filepath = os.path.join(directory, filename)
            structures.append(load_page_structure(filepath))
    return structures
