import json
import os
from pathlib import Path
from datetime import datetime

INPUT_DIR = Path("02_streams_filtered_hololive")
OUTPUT_DIR = Path("03_streams_filtered_hololive_20230101-20251231")

DATE_START = datetime(2023, 1, 1)
DATE_END = datetime(2025, 12, 31)

def parse_date(date_str):
    if date_str is None:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "+00:00").replace("+00:00", ""))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

json_files = sorted(INPUT_DIR.glob("*.json"))

for json_file in json_files:
    with open(json_file, "r", encoding="utf-8") as f:
        streams = json.load(f)

    if not streams:
        continue

    dates = [d for d in (parse_date(s.get("start_actual")) for s in streams if s.get("start_actual")) if d is not None]
    if not dates:
        continue

    min_date = min(dates)
    max_date = max(dates)

    if min_date >= DATE_START:
        print(f"Skipping {json_file.name}: no streams before 2023-01-01")
        continue

    if max_date <= DATE_END:
        print(f"Skipping {json_file.name}: no streams after 2025-12-31")
        continue

    filtered = []
    for s in streams:
        start_actual = s.get("start_actual")
        if not start_actual:
            continue
        parsed = parse_date(start_actual)
        if parsed is None:
            continue
        if DATE_START <= parsed <= DATE_END:
            filtered.append(s)

    output_path = OUTPUT_DIR / json_file.name
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(filtered)} streams to {output_path.name}")
