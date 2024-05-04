import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import unicodedata
import numpy as np
pd.options.mode.chained_assignment = None
import argparse



# Print the result




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

    increment_value = 4
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

# def create_dictionary(gold_df, proportion=1.0):
#     print("method unqiue file id")
#     unique_file_ids = gold_df['file_id'].nunique()
#     keys_to_return = int(unique_file_ids * proportion)
#     total_keys_processed = 0
#     text_toponym_dict = {}
#     for index, row in gold_df.iterrows():
#         file_id = str(row["file_id"])
#         toponym = unicodedata.normalize ('NFD',row["toponym"])
#         geoname_id = row["geoname_id"]
#         in_title = row["in_title"]
#         if total_keys_processed < keys_to_return+1:
#             if file_id not in text_toponym_dict:
#                 text_toponym_dict[file_id] = []
#                 total_keys_processed += 1
#             text_toponym_dict[file_id].append([toponym, geoname_id, in_title])
#     return text_toponym_dict

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

def get_similar_entities(target_toponym, target_rows, surrounding_toponyms, alt_df, country_df, score_dict):
    my_list = set(target_rows['country_code'])

    dict = score_dict
    toponym_set = set(surrounding_toponyms)

    if len(my_list) < 3:
        # print('target toponym country code list:', my_list)
        surrounding_toponyms_country_codes = []
        for toponym in toponym_set:
            candidate_rows_df = get_candidate_rows(alt_df, country_df, toponym)
            for country_code in my_list:
                if (candidate_rows_df['country_code'] == country_code).any():
                    geoname_id_list = list(target_rows[target_rows['country_code'] == country_code]['geonameid'])
                    for geo_id in geoname_id_list:
                        dict[geo_id] += 0.3
                # mask = candidate_rows_df['country_code'].isin([country_code])
                # relevant_rows = candidate_rows_df[mask]
                # if not relevant_rows.empty:

            # for index, candidate_row in candidate_rows_df.iterrows():
            #     if candidate_row['country_code'] in my_list:
            #         geo_id = int(candidate_row['geonameid'])
            #         dict[geo_id] += 1
            #         # Fout: als in canidate_rows meerdere kandidaten dezelfde landcode hebben, dan worden
            #         # er onevenredig veel punten toegkend aan de geo_id.
            #         # oplossing: geoname_ID in dict maar 1 keer per candidate_rows een score toekennen.
            #         # geoname_id_list = list(target_rows[target_rows['country_code'] == candidate_row['country_code']]['geonameid'])
            #         # for geo_id in geoname_id_list:
            #         #     dict[geo_id] += 1
            #         country_codes.append(candidate_row['country_code'])
            # surrounding_toponyms_country_codes.append(country_codes)
    # print(dict)
    return dict
    # print("surrounding_toponyms_country_codes:", surrounding_toponyms_country_codes)




def get_most_likely_candidate_id(country_df, alt_df, target_toponym, surrounding_toponyms, maxpop=False):
    # target_toponym = "Groningen"
    # surrounding_toponyms = ["Kampen", "Paramaribo"]
    candidate_rows_df = get_candidate_rows(alt_df, country_df, target_toponym)

    if candidate_rows_df.empty:
        return ["toponym_not_found"]
    score_dict = create_score_dict(candidate_rows_df)
    score_dict = get_similar_entities(target_toponym, candidate_rows_df, surrounding_toponyms, alt_df, country_df, score_dict)
    popmax_dict = most_populated(candidate_rows_df, score_dict)
    if maxpop:
        if max(popmax_dict.values()) == 0:
            # Executes if none of the candidates have a population or a population of zero.
            return ["population_status_unknown"]
        else:
            # returns the geoname id for the candidate that has the highest population
            # Currently only the candidate with the highest population gets assigned a score
            # that is greater than zero.
            return [max(popmax_dict, key=popmax_dict.get)]
    populated_places_dict = populated_places(candidate_rows_df, popmax_dict)
    dutch_places_dict = dutch_places(candidate_rows_df, populated_places_dict)
    most_likely_geo_id = max(dutch_places_dict, key=dutch_places_dict.get)
    # similar_dict = get_similar_entities(target_toponym, candidate_rows_df, surrounding_toponyms, alt_df, country_df, dutch_places_dict)
    # max_value = max(similar_dict.values())
    # max_keys = [key for key, value in similar_dict.items() if value == max_value]
    # if len(max_keys) > 1:
    #      return ["top candidates have equal scores"]
    # return [max(similar_dict, key=similar_dict.get), similar_dict]
    #

    max_value = max(dutch_places_dict.values())
    max_keys = [key for key, value in dutch_places_dict.items() if value == max_value]
    if len(max_keys) > 1:
         return ["top candidates have equal scores"]
    return [max(dutch_places_dict, key=dutch_places_dict.get), dutch_places_dict]

def analyse_error(guessed_id, actual_id, country_df):
    guessed_row = country_df[country_df['geonameid'] == guessed_id]
    actual_row = country_df[country_df['geonameid'] == actual_id]
    guessed_feature_class = ""
    actual_feature_class = ""
    guessed_feature_code = ""
    actual_feature_code = ""

    if not guessed_row.empty:
        guessed_feature_class = guessed_row['feature_class'].values[0]
        guessed_feature_code = guessed_row['feature_code'].values[0]
        # print(guessed_feature_code)
        # print(guessed_feature_class)
        # print("@@@@@@@")
    if not actual_row.empty:
        actual_feature_class = actual_row['feature_class'].values[0]
        actual_feature_code = actual_row['feature_code'].values[0]
        # print(actual_feature_class)
        # print( "!!!!!!!!")
    if guessed_feature_class == 'A' and actual_feature_class == 'P':
        return "error_code_1"
    if guessed_feature_class == 'P' and actual_feature_class == 'A':
        return "error_code_2"
    if guessed_feature_code == 'ADM1' and actual_feature_code == 'ADM2':
        return "error_code_3"
    if guessed_feature_code == 'ISL' and (actual_feature_class == 'P' or actual_feature_class == 'A'):
        return "error_code_4"
    if actual_feature_code == 'ISL' and (guessed_feature_class == 'P' or guessed_feature_class == 'A'):
        return "error_code_5"
    if actual_feature_code == 'AIRP' and (guessed_feature_class == 'P' or guessed_feature_class == 'A'):
        return "error_code_6"

def populated_places(candidate_rows_df, score_dict):
    P_rows = candidate_rows_df[candidate_rows_df['feature_class'] == 'P']
    geoname_ids = P_rows['geonameid'].tolist()
    for geoname_id in geoname_ids:
        score_dict[geoname_id] += 1.2
    return score_dict







parser = argparse.ArgumentParser()
parser.add_argument("--popmax", action="store_true", help="Perform georesolution with the maximum population as the sole heuristic")
parser.add_argument('--train', action='store_true', help="Run the algorithm on the train set")
parser.add_argument('--test', action='store_true', help="Run the algorithm on the test set")
parser.add_argument("--interactive", action="store_true", help="Prompt user for input")
args = parser.parse_args()
popmax = args.popmax
train = args.train
test = args.test
country_df = load_all_countries("filtered_all_countries.tsv")
alt_df = load_alt_names("filtered_alternative_names.tsv")
if args.interactive:
    user_text = unicodedata.normalize ('NFD',input("Enter a toponym: "))
    candidate_rows_df = get_candidate_rows(alt_df,country_df,user_text)

    print("Candidate toponyms:")
    print(candidate_rows_df[["name", "geonameid", "population", "country_code", "feature_code"]])
    # score_dict = create_score_dict(candidate_rows_df)
    # popmax_dict = most_populated(candidate_rows_df, score_dict)
    # print(popmax_dict)
    # dutch_places_dict = dutch_places(candidate_rows_df, popmax_dict)
    # print(dutch_places_dict)
    quit(0)
if train:
    annotations_df = load_annotations('train_annotations.tsv')
elif test:
    annotations_df = load_annotations('test_annotations.tsv')
else:
    annotations_df = load_annotations('annotations_gold.tsv')

text_toponym_dict =create_dictionary(annotations_df)
total_toponyms = 0
double_count = 0
correctly_guessed = 0
unfound_toponyms = 0
no_pop_status = 0
equal_scores = 0
cntr = 0
error_code_1_count = 0
error_code_2_count = 0
error_code_3_count = 0
error_code_4_count = 0
error_code_5_count = 0
error_code_6_count = 0
other_errors = 0
for file_id in text_toponym_dict:
    for entry in text_toponym_dict[file_id]:
        total_toponyms += 1
        target_toponym = entry[0]
        geoname_id = entry[1]
        surrounding_toponyms = get_surrounding_toponyms(text_toponym_dict[file_id], target_toponym)
        result_list = get_most_likely_candidate_id(country_df, alt_df, target_toponym, surrounding_toponyms, popmax)
        most_likely_candidate_id = result_list[0]
        if len (result_list) > 1:
            score_dict = result_list[1]
            # print(score_dict)
        if str(most_likely_candidate_id) != str(geoname_id):
            error_code = analyse_error(str(most_likely_candidate_id) , str(geoname_id), country_df)
            if error_code == "error_code_1":
                error_code_1_count += 1
                # print(file_id, target_toponym, "actual id:", geoname_id, "guessed id:", most_likely_candidate_id,
                #        sorted(score_dict.items(), key=lambda x: x[1], reverse=True))
            elif error_code == "error_code_2":
                error_code_2_count += 1
            elif error_code == "error_code_3":
                error_code_3_count += 1
            elif error_code == "error_code_4":
                error_code_4_count += 1
            elif error_code == "error_code_5":
                error_code_5_count += 1
            elif error_code == "error_code_6":
                error_code_6_count += 1
            elif most_likely_candidate_id == "toponym_not_found":
                unfound_toponyms += 1
            elif most_likely_candidate_id == "top candidates have equal scores":
                equal_scores += 1
            else:
                other_errors += 1
            #     print(file_id, target_toponym, "actual id:", geoname_id, "guessed id:", most_likely_candidate_id,
            #           sorted(score_dict.items(), key=lambda x: x[1], reverse=True))


            # else:
            #     print(error_code)
            #     print(target_toponym, "actual id:", geoname_id, "guessed id:", most_likely_candidate_id)
            # else:
            #     print(target_toponym, "actual id:", geoname_id, "guessed id:", most_likely_candidate_id,
            #           sorted(score_dict.items(), key=lambda x: x[1], reverse=True))

            # print(target_toponym, "actual id:", geoname_id, "guessed id:", most_likely_candidate_id, sorted(score_dict.items(), key=lambda x:x[1], reverse=True))
        if str(most_likely_candidate_id) == str(geoname_id):
            correctly_guessed += 1
        # if str(most_likely_candidate_id) != str(geoname_id) and most_likely_candidate_id != "toponym_not_found":
        #     print("actual toponym",target_toponym, "guessed geo id", most_likely_candidate_id, "actual id", geoname_id)
        # if most_likely_candidate_id == "toponym_not_found":
        #     # if len(target_toponym.split()) > 1:
        #     #     print("!!!",target_toponym, entry, file_id)
        #     #     cntr += 1
        #
        #     unfound_toponyms += 1
        # if most_likely_candidate_id == "population_status_unknown":
        #     no_pop_status += 1
        # if most_likely_candidate_id == "top candidates have equal scores":
        #     equal_scores += 1


print("Correctly guessed toponyms: {} out of {} total toponyms.".format(correctly_guessed, total_toponyms))

print("Unfound toponyms: {} were not found.".format(unfound_toponyms))
if popmax:
    print("Toponyms without population status: {} didn't have a population status.".format(no_pop_status))
print("Toponyms with equal scores and therefore not correctly guessed: {}".format(equal_scores))
print("Accuracy score: {:.2%}".format(correctly_guessed / total_toponyms))
print("{} toponyms were wrongly guessed as administrative divisions while they were populated places".format(error_code_1_count))
print("{} toponyms were wrongly guessed as populated places while they were administrative divions ".format(error_code_2_count))

print("{} toponyms were wrongly guessed as provincies while they were gemeentes".format(error_code_3_count))
print("{} toponyms were wrongly guessed as islands".format(error_code_4_count))
print("{} toponyms were wrongly guessed as P or A while they were islands".format(error_code_5_count))
print("{} airports where wrongly classified as populated places".format(error_code_6_count))
print("{} toponyms were wrongly classified through an unknown mechanism".format(other_errors))

print("Total amount of wrongly classified or missed toponyms: {}".format(correctly_guessed - total_toponyms))
print(unfound_toponyms+no_pop_status+equal_scores+error_code_1_count+error_code_2_count+error_code_3_count+error_code_4_count+error_code_5_count+error_code_6_count+other_errors)
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
