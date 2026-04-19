from pathlib import Path
import csv

def ensure_data_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
