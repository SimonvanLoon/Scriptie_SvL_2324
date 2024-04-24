import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import unicodedata

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



def most_populated(candidate_rows_df, score_dict):

    # Find the row with the highest population
    candidate_rows_df['population'] = pd.to_numeric(candidate_rows_df['population'], errors='coerce')

    max_population_row = candidate_rows_df.loc[candidate_rows_df['population'].idxmax()]
    most_populated_geoname_id = max_population_row['geonameid']

    # Find the row with the second highest population
    second_max_population_row = candidate_rows_df.loc[candidate_rows_df['population'].nlargest(2).index[-1]]

    # Calculate the population ratio
    population_ratio = max_population_row['population'] / second_max_population_row['population']

    # Assign the score based on population comparison (rounded down to the nearest integer)

    if not pd.isna(population_ratio):
        score = min(int(population_ratio), 10)  # Ensure the score doesn't exceed 10
    else:
        score = 0  # Default score if population_ratio is NaN

    # Update the score for the most populated place
    score_dict[most_populated_geoname_id] = score

    return score_dict


def dutch_places(candidate_rows_df, score_dict):
    # Filter rows where country_code is 'nl' (Dutch)
    dutch_rows = candidate_rows_df[candidate_rows_df['country_code'] == 'NL']
    print(dutch_rows)
    # Add 3 to the score for each geonameid in the filtered rows
    dutch_geoname_ids = dutch_rows['geonameid'].tolist()
    for geoname_id in dutch_geoname_ids:
        score_dict[geoname_id] += 3

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

# Example usage


# Print the updated score dictionary


# Example usage:
# candidate_rows_df = pd.DataFrame(...)
# score_dict = {...}
# updated_score_dict = most_populated(candidate_rows_df, score_dict)
# print(updated_score_dict)




country_df = load_all_countries("filtered_all_countries.tsv")
alt_df = load_alt_names("filtered_alternative_names.tsv")
annotations_df = load_annotations('annotations_gold.tsv')
text_toponym_dict = create_dictionary(annotations_df)
candidate_rows_df = get_candidate_rows(alt_df,country_df,"New York")
print(candidate_rows_df[["population", "geonameid", "country_code", "feature_code"]])
score_dict = create_score_dict(candidate_rows_df)
popmax_dict = most_populated(candidate_rows_df, score_dict)
dutch_places_dict = dutch_places(candidate_rows_df, popmax_dict)
print(dutch_places_dict)

for file_id in text_toponym_dict:
    for entry in text_toponym_dict[file_id]:
        target_toponym = entry [0]

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
