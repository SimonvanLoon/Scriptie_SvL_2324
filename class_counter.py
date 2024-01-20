import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import geocoder
from collections import Counter

# Load the data
gold_df = pd.read_csv("annotations_gold.tsv", sep="\t", header=None,
                      names=["file_id", "toponym", "geoname_id", "in_title"])

# Initialize a Counter object to store the counts
class_counts = Counter()

# Iterate over each row in the DataFrame


# Iterate over each row in the DataFrame
code_dict = {}
request_count = 0
for _, row in gold_df.iterrows():
    if request_count == 500:
        print(code_dict)
        quit()

    # Use the geoname_id to fetch the toponym class
    g = geocoder.geonames(int(row['geoname_id']), key='simonvanloon', method='details')
    request_count += 1
    class_code = g.geojson['features'][0]['properties']['code']
    address = g.geojson['features'][0]['properties']['address']


    # Check if the class code is in the dictionary
    if class_code == 'PPLA':
        print(address)

    if class_code in code_dict:
        # If it is, increment its value by 1
        code_dict[class_code] += 1
    else:
        # If it's not, add it to the dictionary with a value of 1
        code_dict[class_code] = 1

