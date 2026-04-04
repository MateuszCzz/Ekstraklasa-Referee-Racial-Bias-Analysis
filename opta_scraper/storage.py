import json
import re
from pathlib import Path

PARTIAL_DIR  = Path("data/partial")

def ensure_data_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save_json(path: Path, data: dict) -> None:
    path = path.with_name(path.name.lower())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_completed(path: Path) -> tuple[set[str], dict]:
    if not path.exists():
        return set(), {}
    data = load_json(path)
    completed = set(data.get("_completed", []))
    return completed, data

def _clean_text(text: str, max_len: int = 10) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", text)
    return cleaned[:max_len]

def _matchday_number(matchday_name: str) -> str:
    nums = re.findall(r"\d+", matchday_name)
    if nums:
        return nums[0].zfill(2)
    
    return _clean_text(matchday_name, 6)

def save_partial_match(matchday_name: str, match_data: dict) -> Path:
    """Write partial data"""
    md_num    = _matchday_number(matchday_name)
    home_text = _clean_text(match_data.get("home_team", "Unknown"))
    filename  = f"matchday_{md_num}_Game_{home_text}.json".lower()

    dest = PARTIAL_DIR / filename
    save_json(dest, match_data)
    return dest