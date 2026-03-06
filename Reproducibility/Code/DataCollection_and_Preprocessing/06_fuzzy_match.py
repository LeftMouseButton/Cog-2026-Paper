import pandas as pd
import json
import re
from rapidfuzz import fuzz, process

# Tag normalization mapping (after removing parentheticals)
TAG_NORMALIZATION = {
    'role-playing': 'rpg',
    'role playing': 'rpg',
    'action role-playing': 'action rpg',
    'action role playing': 'action rpg',
    'turn-based strategy': 'turn based strategy',
    'turn based strategy': 'turn based strategy',
    'real-time strategy': 'real time strategy',
    'real time strategy': 'real time strategy',
    'real-time tactics': 'real time tactics',
    'real time tactics': 'real time tactics',
    'point and click': 'point and click',
    'point & click': 'point and click',
    'first-person shooter': 'fps',
    'first person shooter': 'fps',
    'third-person shooter': 'third person shooter',
    'third person shooter': 'third person shooter',
    'beat em up': 'beat em up',
    "beat 'em up": 'beat em up',
    'hack and slash': 'hack and slash',
    'hack and slash/beat em up': 'hack and slash',
    'hack and slash/beat \'em up': 'hack and slash',
    'visual novel': 'visual novel',
    'music and rhythm': 'music and rhythm',
    'massively multiplayer': 'massively multiplayer',
    'massively multiplayer online': 'massively multiplayer',
    'free-to-play': 'free to play',
    'free to play': 'free to play',
    'open world': 'open world',
    'open-world': 'open world',
    'singleplayer': 'singleplayer',
    'single player': 'singleplayer',
    'multiplayer': 'multiplayer',
    'multi player': 'multiplayer',
    'co-op': 'co-op',
    'co op': 'co-op',
    'cooperative': 'co-op',
    'local co-op': 'local co-op',
    'local co op': 'local co-op',
    'online co-op': 'online co-op',
    'online co op': 'online co-op',
}

def normalize_tag(tag):
    """Normalize a single tag."""
    tag = tag.lower().strip()
    # Remove parenthetical content for matching (e.g., "Role-playing (RPG)" -> "role-playing")
    tag_base = re.sub(r'\s*\([^)]*\)', '', tag).strip()
    # Check if it matches a known mapping
    if tag_base in TAG_NORMALIZATION:
        return TAG_NORMALIZATION[tag_base]
    if tag in TAG_NORMALIZATION:
        return TAG_NORMALIZATION[tag]
    # Return the cleaned base tag if no mapping
    return tag_base if tag_base else tag

def normalize_tags(tags):
    """Normalize a list of tags."""
    if not tags:
        return []
    normalized = []
    seen = set()
    for tag in tags:
        norm = normalize_tag(tag)
        if norm and norm not in seen:
            normalized.append(norm)
            seen.add(norm)
    return normalized

# Load streamed games
with open('unique_topics.txt', 'r', encoding='utf-8') as f:
    streamed_games = set(line.strip() for line in f if line.strip())
print(f"Total streamed games: {len(streamed_games)}")

# Load IGBD
print("Loading IGBD dataset...")
with open('tag_dataset_igdb.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# Build JSON game dict with tags
json_games = {}
for g in json_data:
    if 'name' not in g:
        continue
    name = g['name']
    tags = []
    if 'keywords' in g:
        tags.extend([kw['name'] for kw in g['keywords'] if 'name' in kw])
    if 'genres' in g:
        tags.extend([gn['name'] for gn in g['genres'] if 'name' in gn])
    if 'themes' in g:
        tags.extend([th['name'] for th in g['themes'] if 'name' in th])
    tags = normalize_tags(tags)
    json_games[name] = tags

json_game_names = list(json_games.keys())
print(f"Games in JSON dataset: {len(json_game_names)}")

# Load tag_dataset_rawg.csv
print("Loading RAWG dataset...")
rawg_df = pd.read_csv('tag_dataset_rawg.csv', usecols=['name', 'tags'], low_memory=False)
# Build RAWG game dict with tags
rawg_games = {}
for _, row in rawg_df.iterrows():
    name = row['name']
    if pd.isna(name):
        continue
    tags = row['tags']
    if pd.isna(tags) or str(tags).strip() == '':
        rawg_games[name] = []
    else:
        rawg_games[name] = normalize_tags(str(tags).split('|'))

rawg_game_names = list(rawg_games.keys())
print(f"Games in RAWG dataset: {len(rawg_game_names)}")

# Filter out games with no tags
json_games_with_tags = {k: v for k, v in json_games.items() if v}
rawg_games_with_tags = {k: v for k, v in rawg_games.items() if v}

print(f"JSON games with tags: {len(json_games_with_tags)}")
print(f"RAWG games with tags: {len(rawg_games_with_tags)}")

# Create lookup dicts with normalized keys
def normalize(s):
    return s.lower().replace('_', ' ').replace('-', ' ').strip()

# Build reverse lookup for exact matches (only games with tags)
json_name_to_key = {normalize(n): n for n in json_games_with_tags.keys()}
rawg_name_to_key = {normalize(n): n for n in rawg_games_with_tags.keys()}

# Find games in both datasets
print("\nFinding games present in both datasets (with tags in both)...")
threshold = 85
matches_in_both = []

for game in streamed_games:
    game_norm = normalize(game)
    
    # Try exact match first
    json_match = json_name_to_key.get(game_norm)
    rawg_match = rawg_name_to_key.get(game_norm)
    
    if json_match and rawg_match:
        # Both exact match
        matches_in_both.append((game, json_match, rawg_match, 100, 100))
    else:
        # Fuzzy match for whichever is missing
        json_fuzzy = None
        rawg_fuzzy = None
        
        if not json_match:
            m = process.extractOne(game, list(json_games_with_tags.keys()), scorer=fuzz.ratio)
            if m and m[1] >= threshold:
                json_fuzzy = m[0]
        
        if not rawg_match:
            m = process.extractOne(game, list(rawg_games_with_tags.keys()), scorer=fuzz.ratio)
            if m and m[1] >= threshold:
                rawg_fuzzy = m[0]
        
        # Check if we have both (one exact, one fuzzy, or both fuzzy)
        final_json = json_match or json_fuzzy
        final_rawg = rawg_match or rawg_fuzzy
        
        if final_json and final_rawg:
            json_score = 100
            rawg_score = 100
            if not json_match:
                m = process.extractOne(game, [final_json], scorer=fuzz.ratio)
                json_score = m[1] if m else 0
            if not rawg_match:
                m = process.extractOne(game, [final_rawg], scorer=fuzz.ratio)
                rawg_score = m[1] if m else 0
            matches_in_both.append((game, final_json, final_rawg, json_score, rawg_score))

print(f"Found {len(matches_in_both)} games in both datasets (with tags)")

# Create output dataframe
output_data = []
for game, json_name, rawg_name, json_score, rawg_score in matches_in_both:
    rawg_tags = rawg_games_with_tags.get(rawg_name, [])
    rawg_tags_str = '|'.join(sorted(rawg_tags)) if rawg_tags else ''
    
    json_tags = json_games_with_tags.get(json_name, [])
    json_tags_str = '|'.join(sorted(json_tags)) if json_tags else ''
    
    output_data.append({
        'topic_id': game,
        'rawg_tags': rawg_tags_str,
        'full_game_tags': json_tags_str
    })

output_df = pd.DataFrame(output_data)
output_df.to_csv('matched.csv', index=False)
print(f"\nSaved matched.csv with {len(output_df)} rows")