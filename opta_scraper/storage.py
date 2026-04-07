import json
import re
from pathlib import Path

PARTIAL_DIR = Path("data/partial")

def ensure_data_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _clean_text(text: str, max_len: int = 10) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", text)
    return cleaned[:max_len]

def _partial_path(matchday_name: str, home_team: str) -> Path:
    nums = re.findall(r"\d+", matchday_name)
    md_num = nums[0].zfill(2) if nums else _clean_text(matchday_name, 6)
    filename = f"matchday_{md_num}_game_{_clean_text(home_team, 10)}.json"
    return PARTIAL_DIR / filename

def save_partial_match(matchday_name: str, match_data: dict) -> Path:
    dest = _partial_path(matchday_name, match_data.get("home_team", "unknown"))
    save_json(dest, match_data)
    return dest

def is_match_done(matchday_name: str, home_team: str) -> bool:
    return _partial_path(matchday_name, home_team).exists()