import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd

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


def most_populated(candidate_rows_df, score_dict):

    # Find the row with the highest population
    candidate_rows_df['population'] = pd.to_numeric(candidate_rows_df['population'], errors='coerce')
    max_population_row = candidate_rows_df.loc[candidate_rows_df['population'].idxmax()]
    most_populated_geoname_id = max_population_row['geonameid']

    # Update the score for the most populated place
    score_dict[most_populated_geoname_id] = 1

    return score_dict



country_df = load_all_countries("filtered_all_countries.tsv")
alt_df = load_alt_names("filtered_alternative_names.tsv")
candidate_rows_df = get_candidate_rows(alt_df,country_df,"China")
print(candidate_rows_df[["population", "geonameid"]])
score_dict = create_score_dict(candidate_rows_df)
print(most_populated(candidate_rows_df, score_dict))


# target_geonameid = str(1814991)
# filtered_row = candidate_rows_df[candidate_rows_df['geonameid'] == target_geonameid]["population"]
# print(filtered_row)
#

# non_zero_population_rows = candidate_rows_df[candidate_rows_df['population'] != str(0)]
# print(non_zero_population_rows["population"])
#
