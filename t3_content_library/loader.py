import os
import yaml


def load_page_structure(filepath: str) -> dict:
    """Load a single page structure definition from a YAML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_page_sets(config_dir: str) -> dict:
    """Load page set definitions from page_sets.yaml."""
    filepath = os.path.join(config_dir, "page_sets.yaml")
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_structures(directory: str, page_set: str | None = None) -> list[dict]:
    """Load all page structure YAML files from a directory, sorted by filename.

    If page_set is specified and not "full", only loads pages matching that set.
    """
    if page_set and page_set != "full":
        config_dir = os.path.dirname(directory)
        sets = load_page_sets(config_dir)
        allowed = sets.get(page_set)
        if allowed is None:
            raise ValueError(f"Unknown page set: {page_set}. Available: {', '.join(sets.keys())}")
        allowed_filenames = {f"{name}.yaml" for name in allowed}
    else:
        allowed_filenames = None

    structures = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            if allowed_filenames and filename not in allowed_filenames:
                continue
            filepath = os.path.join(directory, filename)
            structures.append(load_page_structure(filepath))
    return structures
