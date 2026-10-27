"""Download the free-exercise-db catalog (public domain) into data/exercises/exercises.json."""
import json
import sys
from pathlib import Path

import requests

URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"
OUT = Path(__file__).resolve().parent.parent / "data" / "exercises" / "exercises.json"


def main():
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    data = r.json()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    print(f"Saved {len(data)} exercises -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
