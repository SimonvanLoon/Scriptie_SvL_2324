import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import unicodedata
import numpy as np
pd.options.mode.chained_assignment = None

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

def create_score_dict(candidate_rows_df):
    score_dict = {}
    for index, row in candidate_rows_df.iterrows():
        geoname_id = row['geonameid']
        score_dict[geoname_id] = 0
    return score_dict


# def most_populated(candidate_rows_df, score_dict):
#
#     # Find the row with the highest population
#     candidate_rows_df['population'] = pd.to_numeric(candidate_rows_df['population'], errors='coerce')
#     max_population_row = candidate_rows_df.loc[candidate_rows_df['population'].idxmax()]
#     most_populated_geoname_id = max_population_row['geonameid']
#
#     # Update the score for the most populated place
#     score_dict[most_populated_geoname_id] = 1
#
#     return score_dict

import numpy as np
import pandas as pd

def most_populated(candidate_rows_df, score_dict):
    # Find the row with the highest population
    candidate_rows_df['population'] = pd.to_numeric(candidate_rows_df['population'], errors='coerce')

    max_population_row = candidate_rows_df.loc[candidate_rows_df['population'].idxmax()]
    most_populated_geoname_id = max_population_row['geonameid']

    # Find the row with the second highest population
    second_max_population_row = candidate_rows_df.loc[candidate_rows_df['population'].nlargest(2).index[-1]]


    # Check for zero division
    if second_max_population_row['population'] != 0:
        # Calculate the population ratio
        population_ratio = max_population_row['population'] / second_max_population_row['population']

    else:
        # Handle zero division (set a default value)
        population_ratio = 0

    # Assign the score based on population comparison (rounded down to the nearest integer)
    if not np.isinf(population_ratio) and not np.isnan(population_ratio):
        score = min(int(population_ratio), 10)  # Ensure the score doesn't exceed 10
    else:
        score = 0  # Default score if population_ratio is NaN

    increment_value = 3
    if second_max_population_row['population'] == 0 and max_population_row['population'] != 0:
        score += increment_value

    # Update the score for the most populated place
    score_dict[most_populated_geoname_id] = score

    return score_dict








def dutch_places(candidate_rows_df, score_dict):
    # Filter rows where country_code is 'nl' (Dutch)
    dutch_rows = candidate_rows_df[candidate_rows_df['country_code'] == 'NL']
    # Add 3 to the score for each geonameid in the filtered rows
    dutch_geoname_ids = dutch_rows['geonameid'].tolist()
    for geoname_id in dutch_geoname_ids:
        score_dict[geoname_id] += 2

    return score_dict

def create_dictionary(gold_df):
    text_toponym_dict = {}
    for index, row in gold_df.iterrows():
        file_id = str(row["file_id"])
        toponym = unicodedata.normalize ('NFD',row["toponym"])
        geoname_id = row["geoname_id"]
        in_title = row["in_title"]
        if file_id not in text_toponym_dict:
            text_toponym_dict[file_id] = []
        text_toponym_dict[file_id].append([toponym, geoname_id, in_title])
    return text_toponym_dict


def load_annotations(filename):
    gold_df = pd.read_csv(filename, sep="\t", header=None,
                          names=["file_id", "toponym", "geoname_id", "in_title"])
    return gold_df

def get_surrounding_toponyms(dict_entry, target_toponym):
    surrounding_toponyms = []
    toponym_found = False
    for item in dict_entry:
        toponym = item[0]
        if toponym != target_toponym or (toponym == target_toponym and toponym_found):
            surrounding_toponyms.append(toponym)
        if toponym == target_toponym:
            toponym_found = True
    return surrounding_toponyms

def get_most_likely_candidate_id(country_df, alt_df, target_toponym, surrounding_toponyms, maxpop=False):
    candidate_rows_df = get_candidate_rows(alt_df, country_df, target_toponym)
    if candidate_rows_df.empty:
        return str(0)
    score_dict = create_score_dict(candidate_rows_df)
    popmax_dict = most_populated(candidate_rows_df, score_dict)
    if maxpop:
        return [max(popmax_dict, key=popmax_dict.get)]
    dutch_places_dict = dutch_places(candidate_rows_df, popmax_dict)
    # most_likely_geo_id = max(dutch_places_dict, key=dutch_places_dict.get)
    max_value = max(dutch_places_dict.values())
    max_keys = [key for key, value in dutch_places_dict.items() if value == max_value]
    # if len(max_keys) > 1:
    #     print(target_toponym, dutch_places_dict)
    return max_keys


country_df = load_all_countries("filtered_all_countries.tsv")
alt_df = load_alt_names("filtered_alternative_names.tsv")
annotations_df = load_annotations('annotations_gold.tsv')
text_toponym_dict = create_dictionary(annotations_df)
# candidate_rows_df = get_candidate_rows(alt_df,country_df,"De Pijp")
# print(candidate_rows_df[["population", "geonameid", "country_code", "feature_code"]])
# score_dict = create_score_dict(candidate_rows_df)
# popmax_dict = most_populated(candidate_rows_df, score_dict)
# print(popmax_dict)
# dutch_places_dict = dutch_places(candidate_rows_df, popmax_dict)
# print(dutch_places_dict)

# print(get_most_likely_candidate_id(country_df, alt_df, "De Pijp", [], maxpop=True))

double_count = 0
correctly_guessed = 0
for file_id in text_toponym_dict:
    for entry in text_toponym_dict[file_id]:
        target_toponym = entry[0]
        geoname_id = entry[1]
        surrounding_toponyms = get_surrounding_toponyms(text_toponym_dict[file_id], target_toponym)
        most_likely_candidate_id = get_most_likely_candidate_id(country_df, alt_df, target_toponym, surrounding_toponyms)[0]
        if str(most_likely_candidate_id) == str(geoname_id):
            correctly_guessed += 1
print(correctly_guessed)
#         if len (most_likely_candidate_id) > 1:
#             double_count += 1
#             print(most_likely_candidate_id)
# print(double_count)



# loop through the annotations,
# for every toponym in the annotations, find most likely candidate.
#     if most likely candidate is equal o the toponym in the annotations.
#       correclty_guess_annotations += 1
# accuracy = correclty_guessed annotations / total amount of annotations


# target_geonameid = str(1814991)
# filtered_row = candidate_rows_df[candidate_rows_df['geonameid'] == target_geonameid]["population"]
# print(filtered_row)
#

# non_zero_population_rows = candidate_rows_df[candidate_rows_df['population'] != str(0)]
# print(non_zero_population_rows["population"])
#
