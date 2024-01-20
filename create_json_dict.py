import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import geocoder
import os
import json



# # Write the geoname_dict to a separate json file

def create_pandas_dataframe(tsv_filename):
    gold_df = pd.read_csv(tsv_filename, sep="\t", header=None,
                          names=["file_id", "toponym", "geoname_id", "in_title"])
    invalid_rows = gold_df[pd.to_numeric(gold_df['geoname_id'], errors='coerce').isna()]
    gold_df = gold_df.astype({"geoname_id": 'int'})
    return gold_df


def geoname_id_set(gold_df):
    geoname_ids = set()

    # Loop over all rows and add geoname_id to the set
    for index, row in gold_df.iterrows():
        geoname_ids.add(row['geoname_id'])

    return geoname_ids

def edit_geo_dict(geo_id_set, filename):
    # appends json object to an existing json array.
    with open(filename, 'r') as f:
        data = json.load(f)

        for element in data:
            geonames_id = element['features'][0]["properties"]['geonames_id']
            if geonames_id in geo_id_set:
                print(f"Geonames ID {geonames_id} found in the JSON file.")
            else:
                print(f"Geonames ID {geonames_id} not found in the JSON file.")
        print(len(data))



def create_geo_dict(geo_id_set, filename):
    # creates geonames dictionary when the file does not yet exists
    json_array = []
    for geo_id in geo_id_set:
        geojson = get_geoname_json(geo_id)
        if 'value' in geojson:
            print(geo_id)
            print(geojson['status'])
            json.dump(json_array, f)
            quit()
        else:
            print('succeed')
            json_array.append(geojson)
            print(json_array)
    with open(filename, 'w') as f:
        json.dump(json_array, f)



def get_geoname_json(geoname_id):
    g = geocoder.geonames(geoname_id, key='simonvanloon', method='details')
    return g.geojson

# def create_json_dicts(geo_id_set):
#     geoname_dict = {}
#     if
#     for id in geo_id_set:
#         geoname_dict[id] = 'hello'



def main():
    tsv_filename = "annotations_gold.tsv"
    gold_df = create_pandas_dataframe(tsv_filename)
    geo_id_set = geoname_id_set(gold_df)
    filename = 'geo_dict.json'
    if os.path.exists(filename):
        edit_geo_dict(geo_id_set, filename)
    else:
        create_geo_dict(geo_id_set, filename)






main()