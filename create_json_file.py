import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import json
import os
import geocoder
import math

# Load the dataframe
gold_df = pd.read_csv("annotations_gold.tsv", sep="\t", header=None,
                      names=["file_id", "toponym", "geoname_id", "in_title"])

# Function to get geoname json dictionary
def get_geoname_json(geoname_id):
    # Your code here to get the geoname json dictionary
    g = geocoder.geonames(geoname_id, key='simonvanloon', method='details')
    return g.geojson

# Load the geoname_dict from file if it exists, otherwise create an empty dictionary
if os.path.exists('geoname_dict.json'):
    with open('geoname_dict.json', 'r') as f:
        geoname_dict = json.load(f)
else:
    geoname_dict = {}

# Iterate over each distinct geoname_id in the dataframe
for geoname_id in gold_df['geoname_id'].unique():
    try:
        geoname_id = int(geoname_id)
    except ValueError:
        print(f"Cannot convert geoname_id: {geoname_id} to integer")

    if geoname_id not in geoname_dict:
        print(geoname_id)
        # Get the corresponding geoname json dictionary
        # geoname_json = get_geoname_json(geoname_id)
        #
        #
        # # Store the json dictionary in the geoname_dict
        # geoname_dict[geoname_id] = geoname_json
        #
        # # Write the geoname_dict to a separate json file
        # with open('geoname_dict.json', 'w') as f:
        #     json.dump(geoname_dict, f)
