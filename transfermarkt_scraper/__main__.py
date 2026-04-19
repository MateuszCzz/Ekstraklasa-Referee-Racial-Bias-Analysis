import argparse
from pathlib import Path
from driver import create_driver
from storage import ensure_data_dir, load_csv
from collector import enrich_player_data

BASE_URL = "https://duckduckgo.com/?ia=web&q=%22transfermarkt.com%22"
# path to results from previous segment
FORMATTER_INPUT_DIR = Path("data/optaformatter/result") 
PLAYER_CSV_DIR = FORMATTER_INPUT_DIR / "dimPlayer.csv"
# path to store results 
DATA_DIR = Path("data/transfermarktscraper")
RESULT_DIR = DATA_DIR / "result"

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode")
    
    # arg in
    parser.add_argument(
        "--data-in", 
        type=Path, 
        default=PLAYER_CSV_DIR, 
        metavar="DIR",
        help=f"Directory containing dimPlayer.csv (default: {PLAYER_CSV_DIR})",
        )
    
    #arg out
    parser.add_argument(
        "--data-out",
        type=Path,
        default=RESULT_DIR,
        metavar="DIR",
        help="Where to write results to (default: {RESULT_DIR})",
    )
    args = parser.parse_args()

    output_dir = args.data_out or RESULT_DIR
    ensure_data_dir(output_dir)

    rows = load_csv(Path(args.data_in))
    print(f"Loaded {len(rows)} rows from {args.data_in}")

    driver = create_driver(headless=args.headless)
    try:
        enrich_player_data(driver, BASE_URL)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
