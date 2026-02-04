These folders contain the raw data from the Holodex API, not filtered/cleaned:
streams_raw_hololive_2026feb04/: Subset of streams for channels belonging to the Hololive organization, according to Holodex API.
Acquired this historical stream data (using "get_streams_holodex.py") on Feb 04, 2026 (JST, UTC+9).

denylist.txt: list of stream topics excluded from list of games.

game_tags.csv: list of games/topics from streams, excluding those from denylist.txt, currently untagged.