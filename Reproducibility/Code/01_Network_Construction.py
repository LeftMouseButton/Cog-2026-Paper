#!/usr/bin/env python3
"""
01_Network_Construction.py
Build VTuber collaboration network from symmetric collab pairs CSV.
"""

import argparse
import csv
import math
import os
import pickle

import networkx as nx


def main():
    parser = argparse.ArgumentParser(description='Build VTuber collaboration network')
    parser.add_argument('--input-csv', 
                        default='04_streams_collabs_symmetric/collab_pairs_symmetric.csv',
                        help='Path to symmetric collab pairs CSV')
    parser.add_argument('--lambda-c', type=float, default=0.5,
                        help='Collaboration influence scaling parameter')
    parser.add_argument('--output-dir', default='output/',
                        help='Output directory')
    parser.add_argument('--output', default='network.pkl',
                        help='Output filename')
    args = parser.parse_args()

    input_csv = args.input_csv
    lambda_c = args.lambda_c
    output_dir = args.output_dir
    output_path = os.path.join(output_dir, args.output)

    os.makedirs(output_dir, exist_ok=True)

    print(f"Reading from {input_csv}")

    vtuber_names = set()
    collab_counts = {}

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_name = row['from_name']
            to_name = row['to_name']
            count = int(row['collab_count'])

            vtuber_names.add(from_name)
            vtuber_names.add(to_name)

            key = (from_name, to_name)
            collab_counts[key] = count

    print(f"Loaded {len(vtuber_names)} VTubers")
    print(f"Found {len(collab_counts)} directed edges")

    G = nx.DiGraph()

    for vtuber in vtuber_names:
        G.add_node(vtuber)

    for (u, v), count in collab_counts.items():
        if u != v:
            G.add_edge(u, v, weight=count)
            p_uv = 1 - math.exp(-lambda_c * count)
            G[u][v]['p_uv'] = p_uv

    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    pickle.dump(G, open(output_path, 'wb'))
    print(f"Saved network to {output_path}")


if __name__ == '__main__':
    main()
