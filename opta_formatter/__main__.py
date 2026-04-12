import argparse
from pathlib import Path
from storage import ensure_data_dir, load_json

SCRAPER_INPUT_DIR   = Path("data/optascraper/result")
DATA_DIR = Path("data/optaformatter")
RESULT_DIR = DATA_DIR / "result"

def main() -> None:
    parser = argparse.ArgumentParser()
    # arg in
    parser.add_argument(
        "--data-in", 
        type=Path, 
        default=SCRAPER_INPUT_DIR, 
        metavar="DIR",
        help=f"Directory containing matchdays.json (default: {SCRAPER_INPUT_DIR})",
        )

    #arg out
    parser.add_argument(
        "--data-out",
        type=Path,
        default=RESULT_DIR,
        metavar="DIR",
        help="Where to write result tables (default: {RESULT_DIR})",
    )

    args = parser.parse_args()
    output_dir = args.data_out or RESULT_DIR
    ensure_data_dir(output_dir)

    matchdays = load_json(args.data_in / "matchdays.json")
    if not matchdays:
        print("No matchday.json found, run the scraper first or check your path.")
        return

    # format

    # save

    # print done

if __name__ == "__main__":
    main()
