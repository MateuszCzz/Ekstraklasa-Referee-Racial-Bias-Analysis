import json
import re
from pathlib import Path

DATA_DIR = Path("data/optascraper")
_PL = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")

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
    return re.sub(r"[^A-Za-z0-9]", "", text.translate(_PL))[:max_len]

def _partial_path(matchday_name: str, home_team: str, season: str) -> Path:
    partial_dir = DATA_DIR / season / "partial"
    nums = re.findall(r"\d+", matchday_name)
    md_num = nums[0].zfill(2) if nums else _clean_text(matchday_name, 6)
    filename = f"matchday_{md_num}_game_{_clean_text(home_team, 10)}.json"
    return partial_dir / filename

def save_partial_match(matchday_name: str, match_data: dict, short_home_name: str, season: str) -> Path:
    dest = _partial_path(matchday_name, short_home_name, season)
    save_json(dest, match_data)
    return dest

def load_partial_match(matchday_name: str, home_team: str, season: str) -> dict | None:
    path = _partial_path(matchday_name, home_team, season)
    if path.exists():
        return load_json(path)
    return None

def is_match_done(matchday_name: str, home_team: str, season: str) -> bool:
    return _partial_path(matchday_name, home_team, season).exists()