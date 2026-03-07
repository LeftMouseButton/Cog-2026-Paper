#!/usr/bin/env python3
"""
results.py
Run IC and LT influence maximization models and format results as tables.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PREFERENCES = {
    'RAWG': 'output/preferences_rawg.csv',
    'IGDB': 'output/preferences_igdb.csv',
    'Overlap': 'output/preferences_overlap.csv',
}

MODELS = {
    'Independent Cascade': '03_Independent_Cascade_Model.py',
    'Linear Threshold': '04_Linear_Threshold_Model.py',
}


def run_model(model_script, preferences_path, tags, k, R, alpha=0.5, randseed=42):
    cmd = [
        sys.executable,
        model_script,
        '--preferences', preferences_path,
        '--tags', tags,
        '--k', str(k),
        '--R', str(R),
        '--randseed', str(randseed),
    ]
    if 'Threshold' in model_script:
        cmd.extend(['--alpha', str(alpha)])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr


def parse_results(output):
    spread_match = re.search(r'Expected spread:\s*([\d.]+)', output)
    seeds_match = re.findall(r'\d+\.\s+(\S+)', output)

    spread = float(spread_match.group(1)) if spread_match else None
    seeds = seeds_match[:5] if seeds_match else []

    return spread, seeds


def format_table(results):
    col_widths = [20, 12, 10, 40]
    header = [
        'Model',
        'Preference',
        'Spread',
        'Seeds'
    ]
    separator = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'
    header_line = '|' + '|'.join(
        f' {h:<{col_widths[i]}} ' for i, h in enumerate(header)
    ) + '|'

    lines = [separator, header_line, separator]

    prev_model = None
    for (model, pref, spread, seeds) in results:
        if model != prev_model and prev_model is not None:
            lines.append(separator)
        prev_model = model

        seeds_str = '[' + ', '.join(seeds) + ']' if seeds else '[]'
        spread_str = f'{spread:.2f}' if spread is not None else 'N/A'

        row = f' {model:<{col_widths[0]}} | {pref:<{col_widths[1]}} | {spread_str:<{col_widths[2]}} | {seeds_str:<{col_widths[3]}} '
        lines.append('|' + row + '|')

    lines.append(separator)
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Run influence maximization models and format results')
    parser.add_argument('--tags', default='horror', help='Comma-separated tags')
    parser.add_argument('--k', type=int, default=5, help='Number of seeds')
    parser.add_argument('--R', type=int, default=100, help='Monte Carlo simulations')
    parser.add_argument('--alpha', type=float, default=0.5, help='LT model alpha')
    parser.add_argument('--randseed', type=int, default=42, help='Random seed for reproducibility')
    args = parser.parse_args()

    results = []

    for model_name, model_script in MODELS.items():
        for pref_name, pref_path in PREFERENCES.items():
            if not Path(pref_path).exists():
                print(f"Skipping {pref_path} (not found)", file=sys.stderr)
                continue

            print(f"Running {model_name} with {pref_name}...", file=sys.stderr)
            stdout, stderr = run_model(
                model_script, pref_path, args.tags, args.k, args.R, args.alpha, args.randseed,
            )

            spread, seeds = parse_results(stdout)
            results.append((model_name, pref_name, spread, seeds))

            if spread is None:
                print(f"Warning: Failed to parse results for {model_name} / {pref_name}", file=sys.stderr)
                print(f"stdout: {stdout}", file=sys.stderr)
                print(f"stderr: {stderr}", file=sys.stderr)

    print("\n" + format_table(results))


if __name__ == '__main__':
    main()
