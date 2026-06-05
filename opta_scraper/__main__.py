import argparse
from pathlib import Path
from driver import create_driver
from storage import ensure_data_dir, save_json
from collector import scrape_all_matchdays

DATA_DIR = Path("data/optascraper")
RESULT_DIR = DATA_DIR / "result"
BASE_URLS = [
    {
        "url": "https://optaplayerstats.statsperform.com/en_GB/soccer/ekstraklasa-2024-2025/18h2pva09qsgp7eu1en46pzis/results",
        "season": "2024-25",
    },
    {
        "url": "https://optaplayerstats.statsperform.com/en_GB/soccer/ekstraklasa-2025-2026/3ghh5adz62ws55se0snozmej8/results",
        "season": "2025-26",
    },
]

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode")
    args = parser.parse_args()

    ensure_data_dir(DATA_DIR)
    driver = create_driver(headless=args.headless)
    all_seasons = {}

    try:
        for config in BASE_URLS:
            url, season = config["url"], config["season"]
            print(f"\n\t Season {season}")
            matchdays = scrape_all_matchdays(driver, url, season)

            if not matchdays:
                print(f"  No matchday data found for {season}")
                continue

            all_seasons[season] = matchdays
            print(f"  Done - {sum(len(md) for md in matchdays.values())} matches scraped")
    finally:
        driver.quit()

    if not all_seasons:
        print("No matchday data found - check selectors or page load")
        return

    save_json(RESULT_DIR / "matchdays.json", all_seasons)
    print(f"\nSaved to {RESULT_DIR / 'matchdays.json'}")

if __name__ == "__main__":
    main()
