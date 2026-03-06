#!/usr/bin/env python3
"""
lt_model.py
Linear Threshold diffusion model for VTuber influence maximization.
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


def compute_incoming_weights(G):
    """Compute normalized incoming edge weights b_vu for LT model."""
    b_weights = defaultdict(dict)
    
    for v in G.nodes():
        total_in = sum(G[u][v].get('p_uv', 0.0) for u in G.predecessors(v))
        if total_in > 0:
            for u in G.predecessors(v):
                p_uv = G[u][v].get('p_uv', 0.0)
                b_weights[v][u] = p_uv / total_in
        else:
            for u in G.predecessors(v):
                b_weights[v][u] = 0.0
    
    return b_weights


def simulate_lt(G, seed_set, tag_set, prefs, b_weights, alpha, thresholds):
    """Run one LT diffusion simulation."""
    active = set(seed_set)
    active_list = list(seed_set)
    idx = 0
    
    while idx < len(active_list):
        u = active_list[idx]
        idx += 1
        
        for v in G.successors(u):
            if v not in active:
                influence = sum(b_weights[v].get(w, 0.0) for w in active)
                if influence >= thresholds[v]:
                    active.add(v)
                    active_list.append(v)
    
    return active


def expected_spread(G, seed_set, tag_set, prefs, b_weights, alpha, R):
    """Estimate expected spread via Monte Carlo simulation."""
    nodes = list(G.nodes())
    thresholds = {v: random.random() for v in nodes}
    for v in nodes:
        game_pref = get_game_preference(v, tag_set, prefs)
        thresholds[v] = thresholds[v] * (1 - alpha * game_pref)
    
    spreads = []
    for _ in range(R):
        thresholds = {v: random.random() for v in nodes}
        for v in nodes:
            game_pref = get_game_preference(v, tag_set, prefs)
            thresholds[v] = thresholds[v] * (1 - alpha * game_pref)
        
        activated = simulate_lt(G, seed_set, tag_set, prefs, b_weights, alpha, thresholds)
        spreads.append(len(activated))
    
    return np.mean(spreads)


def greedy_influence_maximization(G, k, tag_set, prefs, b_weights, alpha, R):
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
            spread = expected_spread(G, candidate, tag_set, prefs, b_weights, alpha, R)
            if spread > best_spread:
                best_spread = spread
                best_node = v
        
        if best_node is not None:
            seed_set.append(best_node)
            print(f"  Selected {best_node}: spread = {best_spread:.2f}")
    
    return seed_set, best_spread


def main():
    parser = argparse.ArgumentParser(description='LT model influence maximization')
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
    parser.add_argument('--alpha', type=float, default=0.5,
                        help='Preference influence strength on threshold')
    args = parser.parse_args()
    
    tag_set = [t.strip() for t in args.tags.split(',')]
    
    print(f"Loading data...")
    G, prefs = load_data(args.network, args.preferences)
    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Preferences: {len(prefs)} tags, {len(prefs.columns)} VTubers")
    print(f"Tags: {tag_set}")
    print(f"k={args.k}, R={args.R}, alpha={args.alpha}")
    print()
    
    print("Computing incoming edge weights...")
    b_weights = compute_incoming_weights(G)
    
    print("Running greedy influence maximization...")
    seeds, spread = greedy_influence_maximization(G, args.k, tag_set, prefs, b_weights, args.alpha, args.R)
    
    print()
    print(f"Result: {args.k} recommended seed VTubers")
    print(f"Expected spread: {spread:.2f}")
    for i, s in enumerate(seeds, 1):
        print(f"  {i}. {s}")


if __name__ == '__main__':
    main()
