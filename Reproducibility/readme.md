
## Data:
01_streams_raw_holo_2026Mar05/
- "We collected historical streaming data for VTubers belonging to the organization ``holo'' using the Holodex API"  

02_streams_filtered_hololive/
- "Channels were then manually filtered to include only those affiliated with Hololive Production and to exclude sub-channels, duplicates, and channels not belonging to a unique VTuber (special event channels, music group channels, official company channels)"

03_streams_filtered_hololive_20230101-20251231/
- "The remaining channels were then filtered to include only those VTubers who debuted on or prior to 2023-01-01 and continued their activities until or beyond 2025-12-31"

04_streams_collabs_symmetric/
- "Collaboration data was further processed to ensure consistency. Collaborations are conceptually symmetric events... Accordingly, the collaboration is retained and mirrored rather than discarded, preventing underestimation of influence due to incomplete logging."

04_streams_collabs_symmetric/collab_pairs.csv
- Contains a list of collab pairs and a list of timestamps for when each collab occurred.  
Note: pairs are not symmetric in this file.  
Eg:  
Miko -> Fubuki ...  
Fubuki -> Miko ... does not exist  

04_streams_collabs_symmetric/collab_pairs_symmetric.csv  
- The same file as above, but with each pair mirrored and duplicated.  
eg:   
Miko -> Fubuki ...   
Fubuki -> Miko ...  

excluded_topics.txt
- "while excluding 44 non-videogame topics (such as music covers)"

unique_topics.txt
- we obtained a list of unique topics streamed (as reported by the Holodex api)"

tag_dataset_igdb.json
- "We obtained two videogame tagging/labeling datasets: IGDB and RAWG."

tag_dataset_rawg.csv
- "We obtained two videogame tagging/labeling datasets: IGDB and RAWG."

matched.csv
- "Using fuzzy matching with 85\% similarity, we found a total of 523 topics matching all three sources: the selected VTubers' unique stream topics, and IGDB and RAWG labeling datasets."

## Code: 
### DataCollection and Preprocessing
01_get_streams_holodex.py
- creates 01_streams_raw_holo_2026Mar05/ (automatically set to current date)

(02 is done manually)

03_filter_streams_daterange.py
- creates 03_streams_filtered_hololive_20230101-20251231 

04_symmetricize_collabs.py
- creates 04_streams_collabs_symmetric

05_extract_topics_list.py
- creates unique_topics.txt

06_fuzzy_match.py
- creates matched.csv

### Using the Data

01_Network_Construction.py
- Builds VTuber collaboration network from collab_pairs_symmetric.csv.  
Saves as a .pkl under output/.

02_VTuber_Preference_Modeling.py
- Compute VTuber tag affinity preferences from stream history and tag datasets.  
Saves preferences_*.csv files under output/.  
Input parameter --tag-source', choices=['rawg', 'igdb', 'overlap'], default='rawg'

03_Independent_Cascade_Model.py
- Runs the IC model

04_Linear_Threshold_Model.py
- Runs the LT model

05_Results.py
- Convenience wrapper for running both models, each with all 3 preference csv's, and printing a table  
-> 05_Results.py --tags sandbox --k 1 --R 1000 --randseed 42   
+----------------------+--------------+------------+------------------------------------------+   
| Model                | Preference   | Spread     | Seeds                                    |   
+----------------------+--------------+------------+------------------------------------------+   
| Independent Cascade  | RAWG         | 2.69       | [Shirakami]                              |   
| Independent Cascade  | IGDB         | 1.52       | [Shirakami]                              |  
| Independent Cascade  | Overlap      | 15.89      | [Shirakami]                              |   
+----------------------+--------------+------------+------------------------------------------+   
| Linear Threshold     | RAWG         | 15.19      | [Sakura]                                 |   
| Linear Threshold     | IGDB         | 14.44      | [Sakura]                                 |   
| Linear Threshold     | Overlap      | 17.89      | [Sakura]                                 |   
+----------------------+--------------+------------+------------------------------------------+   
