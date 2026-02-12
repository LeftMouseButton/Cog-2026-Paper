01_streams_raw_hololive_2026feb04/: Subset of raw/unfiltered streams for channels belonging to the Hololive organization, according to Holodex API. Acquired this historical stream data (using "get_streams_holodex.py") on Feb 04, 2026 (JST, UTC+9).
02_streams_filtered_hololive_2026feb04/: Manually filtered to include only individual VTuber channels existing for the full duration from 2023-01-01 to 2025-12-31 (VTubers who "graduated" in or before that timeframe are removed)
03_streams_hololive_2023-01-01_2025-12-31/: Using "filter.py", only streams *started* inside range "2023-01-01 to 2025-12-31" are included.

denylist.txt: list of stream topics excluded from list of games.

game_tags.csv: list of games/topics from streams, excluding those from denylist.txt, currently untagged.
-> python build_game_tags.py --data-dir 03_streams_hololive_2023-01-01_2025-12-31/ --denylist denylist.txt --output game_tags.csv