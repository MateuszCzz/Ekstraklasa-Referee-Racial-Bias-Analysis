import argparse
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor, as_completed

from driver import create_driver
from storage import ensure_data_dir, save_json
from collector import scrape_all_matchdays

DATA_DIR = Path("data")
BASE_URL = "https://optaplayerstats.statsperform.com/en_GB/soccer/ekstraklasa-2024-2025/18h2pva09qsgp7eu1en46pzis/results"


def main() -> None:
    ensure_data_dir(DATA_DIR)

    driver = create_driver(False)
    try:
        matchdays = scrape_all_matchdays(driver, BASE_URL)
    finally:
        driver.quit()

    if not matchdays:
        print("No matchday data found - check selectors or page load")
        return

    save_json(DATA_DIR / "matchdays.json", matchdays)
    print(f"\nSaved to {DATA_DIR / 'matchdays.json'}")

if __name__ == "__main__":
    main()
