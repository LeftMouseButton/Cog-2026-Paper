#!/usr/bin/env python3
"""
02_preference_modeling.py
Compute VTuber tag affinity preferences from stream history.
"""

import argparse
import csv
import json
import math
import os
from collections import defaultdict
from datetime import datetime

import pickle

import networkx as nx
import pandas as pd


def get_vtuber_name_from_json(filepath: str) -> str | None:
    """Extract VTuber english_name from JSON stream data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        streams = json.load(f)
    
    for stream in streams:
        if 'channel' in stream and 'english_name' in stream['channel']:
            return stream['channel']['english_name']
    return None


def main():
    parser = argparse.ArgumentParser(description='Compute VTuber tag preferences')
    parser.add_argument('--network', default='output/network.pkl',
                        help='Path to network pickle file')
    parser.add_argument('--matched-csv', default='matched.csv',
                        help='Path to matched.csv')
    parser.add_argument('--streams-dir', default='04_streams_collabs_symmetric/',
                        help='Directory containing JSON stream files')
    parser.add_argument('--lambda-d', type=float, default=0.1,
                        help='Temporal decay parameter')
    parser.add_argument('--output-dir', default='output/',
                        help='Output directory')
    parser.add_argument('--output', default='preferences.csv',
                        help='Output filename')
    parser.add_argument('--tag-source', choices=['rawg', 'igdb', 'overlap'], default='rawg',
                        help='Tag source: rawg (column 2), igdb (column 3), or overlap (tags in both)')
    args = parser.parse_args()

    network_path = args.network
    matched_csv = args.matched_csv
    streams_dir = args.streams_dir
    lambda_d = args.lambda_d
    output_dir = args.output_dir
    output_path = os.path.join(output_dir, args.output)

    os.makedirs(output_dir, exist_ok=True)

    if args.output == 'preferences.csv':
        args.output = f'preferences_{args.tag_source}.csv'
        output_path = os.path.join(output_dir, args.output)

    G = pickle.load(open(network_path, 'rb'))
    vtubers = list(G.nodes())
    print(f"Loaded network with {len(vtubers)} VTubers")

    topic_to_tags = {}
    with open(matched_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            topic_id = row['topic_id']
            rawg_tags = set(row.get('rawg_tags', '').split('|')) if row.get('rawg_tags') else set()
            igdb_tags = set(row.get('full_game_tags', '').split('|')) if row.get('full_game_tags') else set()
            
            rawg_tags = {t.strip().lower() for t in rawg_tags if t.strip()}
            igdb_tags = {t.strip().lower() for t in igdb_tags if t.strip()}
            
            if args.tag_source == 'rawg':
                tags = rawg_tags
            elif args.tag_source == 'igdb':
                tags = igdb_tags
            else:  # overlap
                tags = rawg_tags & igdb_tags
            
            if tags:
                topic_to_tags[topic_id] = list(tags)

    print(f"Loaded {len(topic_to_tags)} topic-to-tags mappings")

    reference_time = datetime(2025, 12, 31, 23, 59, 59)

    vtuber_tag_affinities = {vt: defaultdict(float) for vt in vtubers}

    json_files = [f for f in os.listdir(streams_dir) if f.endswith('.json')]

    for json_file in json_files:
        filepath = os.path.join(streams_dir, json_file)
        
        vtuber_name = get_vtuber_name_from_json(filepath)
        if not vtuber_name or vtuber_name not in vtubers:
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            streams = json.load(f)

        for stream in streams:
            topic_id = stream.get('topic_id')
            if not topic_id or topic_id not in topic_to_tags:
                continue

            available_at = stream.get('available_at')
            if not available_at:
                continue

            try:
                stream_time = datetime.fromisoformat(available_at.replace('Z', '+00:00'))
                if stream_time.tzinfo is not None:
                    stream_time = stream_time.replace(tzinfo=None)
            except (ValueError, TypeError):
                continue

            days_diff = (reference_time - stream_time).days
            decay = math.exp(-lambda_d * days_diff)

            tags = topic_to_tags[topic_id]
            for tag in tags:
                vtuber_tag_affinities[vtuber_name][tag] += decay

    all_tags = set()
    for affinities in vtuber_tag_affinities.values():
        all_tags.update(affinities.keys())

    all_tags = sorted(all_tags)
    print(f"Found {len(all_tags)} unique tags")

    normalized_affinities = {}

    for vtuber in vtubers:
        affinities = vtuber_tag_affinities[vtuber]
        total = sum(affinities.values())
        if total > 0:
            normalized_affinities[vtuber] = {
                tag: affinities.get(tag, 0) / total
                for tag in all_tags
            }
        else:
            normalized_affinities[vtuber] = {tag: 0.0 for tag in all_tags}

    df = pd.DataFrame(index=all_tags, columns=vtubers)
    for vtuber in vtubers:
        df[vtuber] = [normalized_affinities[vtuber].get(tag, 0.0) for tag in all_tags]

    df.index.name = 'tag'
    df.to_csv(output_path)
    print(f"Saved preferences to {output_path}")
    print(f"Matrix shape: {df.shape} (tags x vtubers)")


if __name__ == '__main__':
    main()
