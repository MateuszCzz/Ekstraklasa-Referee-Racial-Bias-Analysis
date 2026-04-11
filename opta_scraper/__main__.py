import argparse
from pathlib import Path
from driver import create_driver
from storage import ensure_data_dir, save_json
from collector import scrape_all_matchdays

DATA_DIR = Path("data/optascraper")
RESULT_DIR = DATA_DIR / "result"
BASE_URL = "https://optaplayerstats.statsperform.com/en_GB/soccer/ekstraklasa-2024-2025/18h2pva09qsgp7eu1en46pzis/results"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode")
    args = parser.parse_args()

    ensure_data_dir(DATA_DIR)
    driver = create_driver(headless=args.headless)
    try:
        matchdays = scrape_all_matchdays(driver, BASE_URL)
    finally:
        driver.quit()

    if not matchdays:
        print("No matchday data found - check selectors or page load")
        return

    save_json(RESULT_DIR / "matchdays.json", matchdays)
    print(f"\nSaved to {RESULT_DIR / 'matchdays.json'}")

if __name__ == "__main__":
    main()
