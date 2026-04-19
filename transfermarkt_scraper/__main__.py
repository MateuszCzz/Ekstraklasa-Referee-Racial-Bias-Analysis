import argparse
from pathlib import Path
from driver import create_driver
from storage import ensure_data_dir
from collector import enrich_player_data

BASE_URL = "https://www.google.com/search?q=%22transfermarkt.com%22"
FORMATTER_INPUT_DIR = Path("data/optaformatter/result")
DATA_DIR = Path("data/transfermarktscraper")
RESULT_DIR = DATA_DIR / "result"

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode")
    args = parser.parse_args()

    ensure_data_dir(DATA_DIR)
    driver = create_driver(headless=args.headless)
    try:
        enrich_player_data(driver, BASE_URL)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
