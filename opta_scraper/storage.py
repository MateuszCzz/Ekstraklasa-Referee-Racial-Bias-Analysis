import json
import re
from pathlib import Path

DONE_PATH    = Path("data/config/matchesdone.json")
PARTIAL_DIR  = Path("data/partial")

def ensure_data_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save_json(path: Path, data: dict) -> None:
    path = path.with_name(path.name.lower())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

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

def _done_key(match_data: dict) -> str:
    """create done id for a match date_hometeam_awayteam"""
    date      = re.sub(r"[^A-Za-z0-9]", "", match_data.get("date", "nodate"))
    home_slug = _clean_text(match_data.get("home_team", "unknown"), 50)
    away_slug = _clean_text(match_data.get("away_team", "unknown"), 50)
    return f"{date}_{home_slug}_{away_slug}"

def load_done_matches() -> dict:
    """Load the done-matches registry; returns {} if file missing."""
    if not DONE_PATH.exists():
        return {}
    return load_json(DONE_PATH)

def is_match_done(match_data: dict, done_registry: dict) -> bool:
    return _done_key(match_data) in done_registry

def mark_match_done(match_data: dict, done_registry: dict) -> None:
    """Add the match to the in-memory registry and persist it."""
    key = _done_key(match_data)
    done_registry[key] = {
        "date":      match_data.get("date"),
        "home_team": match_data.get("home_team"),
        "away_team": match_data.get("away_team"),
        "matchday":  match_data.get("matchday"),
    }
    save_json(DONE_PATH, done_registry)