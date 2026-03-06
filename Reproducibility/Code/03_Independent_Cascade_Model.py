#!/usr/bin/env python3
"""
ic_model.py
Independent Cascade diffusion model for VTuber influence maximization.
"""

import argparse
import pickle
import random
from collections import defaultdict

import numpy as np
import pandas as pd


def load_data(network_path, preferences_path):
    """Load network and preferences."""
    G = pickle.load(open(network_path, 'rb'))
    prefs = pd.read_csv(preferences_path)
    prefs = prefs.set_index('tag')
    return G, prefs


def get_game_preference(vtuber, tag_set, prefs):
    """Compute game_preference(v, T^h) = average tag affinity."""
    vtuber_cols = [col for col in prefs.columns if vtuber.lower() in col.lower()]
    if not vtuber_cols:
        return 0.0
    vtuber_col = vtuber_cols[0]
    
    affinities = []
    for tag in tag_set:
        if tag in prefs.index:
            affinities.append(prefs.loc[tag, vtuber_col])
        else:
            affinities.append(0.0)
    
    if not affinities:
        return 0.0
    return np.mean(affinities)


def get_p_act(u, v, G, tag_set, prefs):
    """Compute p_act(u -> v, T^h) = p_uv * game_preference(v, T^h)."""
    if not G.has_edge(u, v):
        return 0.0
    p_uv = G[u][v].get('p_uv', 0.0)
    game_pref = get_game_preference(v, tag_set, prefs)
    return p_uv * game_pref


def simulate_ic(G, seed_set, tag_set, prefs):
    """Run one IC diffusion simulation."""
    active = set(seed_set)
    newly_active = set(seed_set)
    
    while newly_active:
        next_active = set()
        for u in newly_active:
            for v in G.successors(u):
                if v not in active:
                    p_act = get_p_act(u, v, G, tag_set, prefs)
                    if random.random() < p_act:
                        next_active.add(v)
        active |= next_active
        newly_active = next_active
    
    return active


def expected_spread(G, seed_set, tag_set, prefs, R):
    """Estimate expected spread via Monte Carlo simulation."""
    spreads = []
    for _ in range(R):
        activated = simulate_ic(G, seed_set, tag_set, prefs)
        spreads.append(len(activated))
    return np.mean(spreads)


def greedy_influence_maximization(G, k, tag_set, prefs, R):
    """Greedy algorithm for influence maximization."""
    nodes = list(G.nodes())
    seed_set = []
    
    for _ in range(k):
        best_node = None
        best_spread = -1
        
        for v in nodes:
            if v in seed_set:
                continue
            candidate = seed_set + [v]
            spread = expected_spread(G, candidate, tag_set, prefs, R)
            if spread > best_spread:
                best_spread = spread
                best_node = v
        
        if best_node is not None:
            seed_set.append(best_node)
            print(f"  Selected {best_node}: spread = {best_spread:.2f}")
    
    return seed_set, best_spread


def main():
    parser = argparse.ArgumentParser(description='IC model influence maximization')
    parser.add_argument('--preferences', default='output/preferences_igdb.csv',
                        help='Path to preferences CSV')
    parser.add_argument('--network', default='output/network.pkl',
                        help='Path to network pickle')
    parser.add_argument('--tags', default='action,rpg',
                        help='Comma-separated tag set')
    parser.add_argument('--k', type=int, default=5,
                        help='Number of seeds to select')
    parser.add_argument('--R', type=int, default=100,
                        help='Number of Monte Carlo simulations')
    args = parser.parse_args()
    
    tag_set = [t.strip() for t in args.tags.split(',')]
    
    print(f"Loading data...")
    G, prefs = load_data(args.network, args.preferences)
    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Preferences: {len(prefs)} tags, {len(prefs.columns)} VTubers")
    print(f"Tags: {tag_set}")
    print(f"k={args.k}, R={args.R}")
    print()
    
    print("Running greedy influence maximization...")
    seeds, spread = greedy_influence_maximization(G, args.k, tag_set, prefs, args.R)
    
    print()
    print(f"Result: {args.k} recommended seed VTubers")
    print(f"Expected spread: {spread:.2f}")
    for i, s in enumerate(seeds, 1):
        print(f"  {i}. {s}")


if __name__ == '__main__':
    main()
