import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import unicodedata
import json
import time


def load_alt_names(filename):
    gold_df = pd.read_csv(filename, sep="\t", header=None, encoding='utf-8')
    column_names = [
        'alternateNameId',
        'geonameid',
        'isolanguage',
        'alternate name',
        'isPreferredName',
        'isShortName',
        'isColloquial',
        'isHistoric',
        'from',
        'to'
    ]

    gold_df.columns = column_names
    return gold_df
def load_all_countries(filename):
    df = pd.read_csv(filename, sep="\t", header=None, encoding='utf-8')
    column_names = [
        "geonameid",
        "name",
        "asciiname",
        "alternatenames",
        "latitude",
        "longitude",
        "feature_class",
        "feature_code",
        "country_code",
        "cc2",
        "admin1_code",
        "admin2_code",
        "admin3_code",
        "admin4_code",
        "population",
        "elevation",
        "dem",
        "timezone",
        "modification_date"
    ]
    df.columns = column_names
    return df

def get_candidate_rows(alt_df, country_df, toponym):
    # Step 1: Filter alternate names DataFrame
    alt_toponym_df = alt_df[alt_df['alternate name'] == toponym]

    # Step 2: Filter main country DataFrame
    single_toponym_df = country_df[
        (country_df['name'] == toponym) |
        (country_df['geonameid'].isin(alt_toponym_df['geonameid']))
    ]
    return single_toponym_df

def load_annotations(filename):
    gold_df = pd.read_csv(filename, sep="\t", header=None,
                          names=["file_id", "toponym", "geoname_id", "in_title"])
    return gold_df

def create_toponym_set(gold_df):
    toponym_set = set()
    for index, row in gold_df.iterrows():
        toponym = unicodedata.normalize ('NFD',row["toponym"])
        toponym_set.add(toponym)
    return toponym_set

gold_df = load_annotations('annotations_gold.tsv')
toponym_set = create_toponym_set(gold_df)
country_df = load_all_countries("filtered_all_countries.tsv")
alt_df = load_alt_names("filtered_alternative_names.tsv")
toponym_candidates_dict = {}
start_time = time.time()

# for index, row in gold_df.iterrows():
#     toponym = unicodedata.normalize('NFD', row["toponym"])
#     candidate_df = get_candidate_rows(alt_df, country_df, toponym).to_dict()
#     toponym_candidates_dict[toponym] = candidate_df

for toponym in toponym_set:
    toponym = unicodedata.normalize('NFD', toponym)
    candidate_df = get_candidate_rows(alt_df, country_df, toponym).to_dict()
    toponym_candidates_dict[toponym] = candidate_df
with open("toponym_candidates.json", "w") as outfile:
    json.dump(toponym_candidates_dict, outfile)

with open('toponym_candidates.json') as json_file:
    data = json.load(json_file)
    # for entry in data:
    #     print(pd.DataFrame(data["Oekraïne"]))
    #     quit()
target_toponym = unicodedata.normalize('NFD', "Oekraïne")
print(pd.DataFrame(data[target_toponym]))
end_time = time.time()
elapsed_time = end_time - start_time

print(elapsed_time)