import argparse
import json
from .pipeline import run_fixture


def main():
    parser = argparse.ArgumentParser(description="DCI synthetic fixture replay; shadow only")
    parser.add_argument("fixture")
    parser.add_argument("--journal", help="Dedicated local SQLite shadow journal (optional)")
    args = parser.parse_args()
    print(json.dumps(run_fixture(args.fixture, args.journal), indent=2))


if __name__ == "__main__":
    main()
