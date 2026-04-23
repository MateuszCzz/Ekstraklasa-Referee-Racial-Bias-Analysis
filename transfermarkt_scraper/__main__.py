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
PLAYER_URL_MAP = "players_url_map.csv"

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

    #arg test
    parser.add_argument(
        "--test",
        type=bool,
        default=False,
        metavar="DIR",
        help="Limit operations to first 3 rows for a test run (default: {False})",
    )
    args = parser.parse_args()

    output_dir = args.data_out or RESULT_DIR
    ensure_data_dir(output_dir)

    players = load_csv(Path(args.data_in))
    print(f"Loaded {len(players)} rows from {args.data_in}")

    try:
        players_url_cached = load_csv(path= DATA_DIR / PLAYER_URL_MAP)
        print(f"Loaded {len(players_url_cached)} rows from {DATA_DIR / PLAYER_URL_MAP}")
    except FileNotFoundError:
        print(f"Player cached url file not found at {DATA_DIR / PLAYER_URL_MAP}, skipping.")

    driver = create_driver(headless=args.headless)
    try:
            enriched = enrich_player_data(
                 driver, 
                 BASE_URL, 
                 test_mode = args.test, 
                 players = players, 
                 url_cached=players_url_cached 
                 )

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
