import json
from pathlib import Path

INPUT_DIR = Path("04_streams_collabs_symmetric")
EXCLUDED_FILE = Path("excluded_topics.txt")
OUTPUT_FILE = Path("unique_topics.txt")

def load_excluded_topics():
    if EXCLUDED_FILE.exists():
        with open(EXCLUDED_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def load_existing_topics():
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

excluded_topics = load_excluded_topics()
existing_topics = load_existing_topics()
new_topics = set()

json_files = sorted(INPUT_DIR.glob("*.json"))

for json_file in json_files:
    with open(json_file, "r", encoding="utf-8") as f:
        streams = json.load(f)
    
    for stream in streams:
        topic_id = stream.get("topic_id")
        if not topic_id:
            continue
        if topic_id in excluded_topics:
            continue
        if topic_id not in existing_topics and topic_id not in new_topics:
            new_topics.add(topic_id)

if new_topics:
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for topic in sorted(new_topics):
            f.write(f"{topic}\n")
    print(f"Added {len(new_topics)} new topics to {OUTPUT_FILE}")
else:
    print("No new topics to add")
