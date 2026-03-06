#!/usr/bin/env python3
"""
04_symmetricize_collabs.py
Handle inconsistent collab data across VTuber files:
1. Both files have collab -> Deduplicate
2. One file only -> Distinguish legitimate single-sided vs incomplete logging

Uses time overlap to match collabs between VTubers.
"""

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Optional


def load_streams(streams_dir: str) -> tuple[dict, dict]:
    """Load all streams from JSON files in directory.
    
    Returns:
        Tuple of (vtuber_streams, vtuber_names) where:
        - vtuber_streams: Dict mapping channel_id -> list of stream dicts
        - vtuber_names: Dict mapping channel_id -> vtuber name
    """
    json_files = [f for f in os.listdir(streams_dir) if f.endswith('.json')]
    print(f"Found {len(json_files)} JSON files")
    
    vtuber_streams = {}
    vtuber_names = {}
    
    for json_file in json_files:
        filepath = os.path.join(streams_dir, json_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            streams = json.load(f)
        
        channel_id = None
        vtuber_name = None
        for stream in streams:
            if 'channel' in stream:
                channel_id = stream['channel'].get('id')
                vtuber_name = stream['channel'].get('english_name')
                break
        
        if channel_id:
            vtuber_streams[channel_id] = streams
            vtuber_names[channel_id] = vtuber_name
    
    print(f"Loaded {len(vtuber_streams)} VTubers")
    return vtuber_streams, vtuber_names


def parse_timestamp(ts_str) -> Optional[datetime]:
    """Parse ISO timestamp string to datetime."""
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(str(ts_str).replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def streams_overlap(stream_a: dict, stream_b: dict) -> bool:
    """Check if two streams have overlapping time periods.
    
    Overlap exists if: stream_a.start <= stream_b.end AND stream_b.start <= stream_a.end
    """
    start_a = parse_timestamp(stream_a.get('start_actual'))
    end_a = parse_timestamp(stream_a.get('end_actual'))
    start_b = parse_timestamp(stream_b.get('start_actual'))
    end_b = parse_timestamp(stream_b.get('end_actual'))
    
    if not all([start_a, end_a, start_b, end_b]):
        return False
    
    return bool(start_a and end_a and start_b and end_b and start_a <= end_b and start_b <= end_a)


def extract_collab_entries(vtuber_streams: dict, vtuber_names: dict) -> list[dict]:
    """Extract all collab entries from all VTuber streams.
    
    Returns list of:
    {
        'host_channel_id': str,
        'host_name': str,
        'collab_channel_id': str,
        'collab_name': str,
        'stream_id': str,
        'start_actual': datetime,
        'end_actual': datetime,
    }
    """
    collab_entries = []
    
    for channel_id, streams in vtuber_streams.items():
        host_name = vtuber_names.get(channel_id, 'Unknown')
        
        for stream in streams:
            collabs = stream.get('collabs', [])
            if not collabs:
                continue
            
            start_actual = parse_timestamp(stream.get('start_actual'))
            end_actual = parse_timestamp(stream.get('end_actual'))
            stream_id = stream.get('id')
            
            for collab in collabs:
                collab_channel_id = collab.get('id')
                collab_name = vtuber_names.get(collab_channel_id, collab.get('name', 'Unknown'))
                
                if collab_channel_id and collab_channel_id in vtuber_names:
                    collab_entries.append({
                        'host_channel_id': channel_id,
                        'host_name': host_name,
                        'collab_channel_id': collab_channel_id,
                        'collab_name': collab_name,
                        'stream_id': stream_id,
                        'start_actual': start_actual,
                        'end_actual': end_actual,
                    })
    
    print(f"Extracted {len(collab_entries)} collab entries")
    return collab_entries


def symmetricize_collabs(collab_entries: list[dict], vtuber_streams: dict) -> dict:
    """Match collabs across VTubers using time overlap and deduplicate.
    
    Returns:
        Dict mapping (min_id, max_id) -> {
            'count': int,
            'source': 'both' | 'single',
            'timestamps': list[str],
            'vtuber_a': str,
            'vtuber_b': str,
        }
    """
    matched_pairs = {}  # (host_a, collab_b) -> list of entry dicts
    matched_stream_ids = set()  # Track which stream entries have been matched
    
    for entry in collab_entries:
        host_id = entry['host_channel_id']
        collab_id = entry['collab_channel_id']
        key = (host_id, collab_id)
        
        if key not in matched_pairs:
            matched_pairs[key] = []
        matched_pairs[key].append(entry)
    
    symmetric_collabs = {}
    
    for (host_id, collab_id), entries in matched_pairs.items():
        sorted_ids = tuple(sorted([host_id, collab_id]))
        
        reverse_key = (collab_id, host_id)
        
        if reverse_key in matched_pairs:
            entries_from_both = True
            other_entries = matched_pairs[reverse_key]
            
            all_entries = entries + other_entries
            matched_entries = []
            
            for entry_a in entries:
                for entry_b in other_entries:
                    if streams_overlap(entry_a, entry_b):
                        matched_entries.append({
                            'timestamp': entry_a['start_actual'].isoformat() if entry_a['start_actual'] else None,
                            'host_a': entry_a['host_channel_id'],
                            'host_b': entry_b['host_channel_id'],
                        })
                        break
            
            source = 'both'
        else:
            all_entries = entries
            source = 'single'
            
            matched_entries = []
            for entry in all_entries:
                matched_entries.append({
                    'timestamp': entry['start_actual'].isoformat() if entry['start_actual'] else None,
                    'host': entry['host_channel_id'],
                })
        
        timestamps = [m['timestamp'] for m in matched_entries if m['timestamp']]
        
        vtuber_a = entries[0]['host_name'] if entries else 'Unknown'
        vtuber_b = entries[0]['collab_name'] if entries else 'Unknown'
        
        if sorted_ids in symmetric_collabs:
            symmetric_collabs[sorted_ids]['count'] += len(matched_entries)
            symmetric_collabs[sorted_ids]['timestamps'].extend(timestamps)
        else:
            symmetric_collabs[sorted_ids] = {
                'count': len(matched_entries),
                'source': source,
                'timestamps': timestamps,
                'vtuber_a': vtuber_a,
                'vtuber_b': vtuber_b,
            }
    
    return symmetric_collabs


def save_output(symmetric_collabs: dict, output_dir: str):
    """Save symmetric collab data to output directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    collab_pairs = []
    for (id_a, id_b), data in symmetric_collabs.items():
        collab_pairs.append({
            'vtuber_a_id': id_a,
            'vtuber_b_id': id_b,
            'vtuber_a_name': data['vtuber_a'],
            'vtuber_b_name': data['vtuber_b'],
            'collab_count': data['count'],
            'source': data['source'],
            'timestamps': json.dumps(data['timestamps']),
        })
    
    collab_pairs.sort(key=lambda x: (-x['collab_count'], x['vtuber_a_name'], x['vtuber_b_name']))
    
    output_csv = os.path.join(output_dir, 'collab_pairs.csv')
    with open(output_csv, 'w', encoding='utf-8') as f:
        f.write('vtuber_a_id,vtuber_b_id,vtuber_a_name,vtuber_b_name,collab_count,source,timestamps\n')
        for pair in collab_pairs:
            f.write(f'"{pair["vtuber_a_id"]}","{pair["vtuber_b_id"]}","{pair["vtuber_a_name"]}","{pair["vtuber_b_name"]}",{pair["collab_count"]},"{pair["source"]}","{pair["timestamps"]}"\n')
    
    print(f"Saved {len(collab_pairs)} collab pairs to {output_csv}")
    
    save_output_symmetric(collab_pairs, output_dir)
    
    summary = defaultdict(int)
    for data in symmetric_collabs.values():
        summary[data['source']] += 1
    print(f"Summary: {dict(summary)}")
    
    total_collabs = sum(data['count'] for data in symmetric_collabs.values())
    print(f"Total collabs: {total_collabs}")


def save_output_symmetric(collab_pairs: list[dict], output_dir: str):
    """Save symmetric collab data with mirrored pairs (A->B and B->A)."""
    
    symmetric_pairs = []
    for pair in collab_pairs:
        original = {
            'from_id': pair['vtuber_a_id'],
            'to_id': pair['vtuber_b_id'],
            'from_name': pair['vtuber_a_name'],
            'to_name': pair['vtuber_b_name'],
            'collab_count': pair['collab_count'],
            'source': pair['source'],
            'timestamps': pair['timestamps'],
        }
        mirrored = {
            'from_id': pair['vtuber_b_id'],
            'to_id': pair['vtuber_a_id'],
            'from_name': pair['vtuber_b_name'],
            'to_name': pair['vtuber_a_name'],
            'collab_count': pair['collab_count'],
            'source': pair['source'],
            'timestamps': pair['timestamps'],
        }
        symmetric_pairs.append(original)
        symmetric_pairs.append(mirrored)
    
    symmetric_pairs.sort(key=lambda x: (-x['collab_count'], x['from_name'], x['to_name']))
    
    output_csv = os.path.join(output_dir, 'collab_pairs_symmetric.csv')
    with open(output_csv, 'w', encoding='utf-8') as f:
        f.write('from_id,to_id,from_name,to_name,collab_count,source,timestamps\n')
        for pair in symmetric_pairs:
            f.write(f'"{pair["from_id"]}","{pair["to_id"]}","{pair["from_name"]}","{pair["to_name"]}",{pair["collab_count"]},"{pair["source"]}","{pair["timestamps"]}"\n')
    
    print(f"Saved {len(symmetric_pairs)} symmetric edges to {output_csv}")


def main():
    parser = argparse.ArgumentParser(description='Symmetricize VTuber collaboration data')
    parser.add_argument('--streams-dir', 
                        default='03_streams_filtered_hololive_20230101-20251231/',
                        help='Directory containing source JSON stream files')
    parser.add_argument('--output-dir', 
                        default='04_streams_collabs_symmetric/',
                        help='Output directory for symmetric collab data')
    args = parser.parse_args()
    
    print("Loading streams...")
    vtuber_streams, vtuber_names = load_streams(args.streams_dir)
    
    print("Extracting collab entries...")
    collab_entries = extract_collab_entries(vtuber_streams, vtuber_names)
    
    print("Symmetricizing collabs (matching by time overlap)...")
    symmetric_collabs = symmetricize_collabs(collab_entries, vtuber_streams)
    
    print("Saving output...")
    save_output(symmetric_collabs, args.output_dir)


if __name__ == '__main__':
    main()
