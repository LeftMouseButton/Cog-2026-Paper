import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

INPUT_DIR = Path("03_streams_filtered_hololive_20230101-20251231")
OUTPUT_DIR = Path("04_streams_collabs_symmetric")

def parse_date(date_str):
    if date_str is None:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "+00:00").replace("+00:00", ""))

def streams_overlap(start1, end1, start2, end2, tolerance_minutes=15):
    if None in (start1, end1, start2, end2):
        return False
    max_start = max(start1, start2)
    min_end = min(end1, end2)
    if max_start > min_end:
        return False
    overlap = (min_end - max_start).total_seconds()
    duration1 = (end1 - start1).total_seconds()
    duration2 = (end2 - start2).total_seconds()
    min_duration = min(duration1, duration2)
    return overlap >= min_duration * 0.5

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

json_files = sorted(INPUT_DIR.glob("*.json"))

all_data = {}
channel_ids = set()

for json_file in json_files:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not data:
        continue
    
    channel_id = data[0]["channel"]["id"]
    all_data[channel_id] = {
        "filename": json_file.name,
        "streams": data
    }
    channel_ids.add(channel_id)

print(f"Loaded {len(all_data)} channel files")

stream_index = defaultdict(list)

for channel_id, channel_data in all_data.items():
    for stream in channel_data["streams"]:
        start = parse_date(stream.get("start_actual"))
        end = parse_date(stream.get("end_actual"))
        if start and end:
            stream_index[channel_id].append({
                "stream": stream,
                "start": start,
                "end": end
            })

corrections_made = 0

for channel_id, channel_data in all_data.items():
    modified = False
    
    for stream in channel_data["streams"]:
        start = parse_date(stream.get("start_actual"))
        end = parse_date(stream.get("end_actual"))
        if not start or not end:
            continue
        
        collabs = stream.get("collabs", [])
        existing_collab_ids = {c["id"] for c in collabs}
        
        for collab in collabs:
            collab_id = collab["id"]
            
            if collab_id not in stream_index:
                continue
            
            found_reciprocal = False
            
            for other_stream_info in stream_index[collab_id]:
                other_stream = other_stream_info["stream"]
                other_start = other_stream_info["start"]
                other_end = other_stream_info["end"]
                
                if streams_overlap(start, end, other_start, other_end):
                    other_collabs = other_stream.get("collabs", [])
                    other_collab_ids = {c["id"] for c in other_collabs}
                    
                    if channel_id not in other_collab_ids:
                        other_collabs.append({
                            "id": channel_id,
                            "name": stream["channel"]["name"],
                            "duration_seconds": collab.get("duration_seconds")
                        })
                        other_stream["collabs"] = other_collabs
                        corrections_made += 1
                        modified = True
                        print(f"Added collab: {channel_id} -> {collab_id} in stream {other_stream.get('id')}")
                    
                    found_reciprocal = True
                    break
            
            if not found_reciprocal:
                pass

print(f"Total corrections made: {corrections_made}")

for channel_id, channel_data in all_data.items():
    output_path = OUTPUT_DIR / channel_data["filename"]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(channel_data["streams"], f, ensure_ascii=False, indent=2)

print(f"Wrote {len(all_data)} files to {OUTPUT_DIR}")
