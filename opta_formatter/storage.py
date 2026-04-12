import json
from pathlib import Path

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_data_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)