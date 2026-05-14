from pathlib import Path
import csv
from PIL import Image

def ensure_data_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save_csv(path: Path, rows: list[dict], fieldnames: list[str], mode: str = "w") -> None:
    write_header = mode == "w" or not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)

def save_image(path: Path, image: Image.Image, name: str, quality: int = 90) -> None:
    path.mkdir(parents=True, exist_ok=True)
    image.save(path / f"{name}.jpg", format="JPEG", quality=quality)
