import json
from pathlib import Path
import pandas as pd

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_data_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save_tables(tables: dict[str, pd.DataFrame], data_out: Path) -> None:
    ensure_data_dir(data_out)
    for name, df in tables.items():
        path = data_out / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"  {path.name:<35} ({df.shape[0]} rows × {df.shape[1]} cols)")

