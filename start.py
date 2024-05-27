import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import unicodedata
import numpy as np
pd.options.mode.chained_assignment = None
import argparse
import time
from parameters import Parameters
import json
# Print the result

with open('toponym_candidates.json') as json_file:
    data = json.load(json_file)



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

def create_score_dict(candidate_rows_df):
    score_dict = {}
    for index, row in candidate_rows_df.iterrows():
        geoname_id = row['geonameid']
        score_dict[geoname_id] = 0
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

class GetCandidate:
    def __init__(self, target_toponym, surrounding_toponyms, parameters_obj, alt_df):
        self.surrounding_toponyms = surrounding_toponyms
        self.candidate_rows_df = pd.DataFrame(data[target_toponym])
        self.score_dict = create_score_dict(self.candidate_rows_df)
        self.params = parameters_obj
        self.alt_df = alt_df

    def get_most_likely_candidate(self, maxpop=False):
        if self.candidate_rows_df.empty:
            return ["toponym_not_found"]
        if self.candidate_rows_df.shape[0] == 1:
            geoname_id = self.candidate_rows_df.iloc[0]['geonameid']
            return [geoname_id]
        self.population_size()
        if maxpop:
            if max(self.score_dict.values()) == 0:
                # Executes if none of the candidates have a population or a population of zero.
                return ["population_status_unknown"]
            else:
                # returns the geoname id for the candidate that has the highest population
                # Currently only the candidate with the highest population gets assigned a score
                # that is greater than zero.
                return [max(self.score_dict, key=self.score_dict.get)]
        if self.params.get_sim_entity_value() != 0:
            self.country_similarity()
        self.superordinate_mention()
        self.p_class_places()
        self.dutch_places()
        self.feature_rank()
        max_value = max(self.score_dict.values())
        max_keys = [key for key, value in self.score_dict.items() if value == max_value]
        if len(max_keys) > 1:
            code = self.most_populated_place(max_keys)
            if code == "no_population":
                code = self.most_alt_names(max_keys)
                if code == "no_alt_names":
                    return ["top candidates have equal scores", self.score_dict]
                else:
                    return [code, self.score_dict]
                # return ["top candidates have equal scores", dutch_places_dict]
            else:
                return [code, self.score_dict]
        return [max(self.score_dict, key=self.score_dict.get), self.score_dict]

    def population_size(self):
        #    Find the row with the highest population
        self.candidate_rows_df['population'] = pd.to_numeric(self.candidate_rows_df['population'], errors='coerce')
        sorted_rows = self.candidate_rows_df.nlargest(2, 'population')
        max_population_row = self.candidate_rows_df.loc[sorted_rows.index[0]]
        most_populated_geoname_id = max_population_row['geonameid']

        # Find the row with the second highest population
        # The '-1' index ensures that a row is always selected even if there is only one candidate row
        second_max_population_row = self.candidate_rows_df.loc[sorted_rows.index[-1]]

        # Check for zero division
        if second_max_population_row['population'] != 0:
            # Calculate the population ratio
            population_ratio = max_population_row['population'] / second_max_population_row['population']
            # if population_ratio > 5
            #     print( candidate_rows_df[['population', 'geonameid', 'name']])
            #     print(most_populated_geoname_id, second_max_population_row['geonameid'] )

        else:
            # Handle zero division (set a default value)
            population_ratio = 0

        # Assign the score based on population comparison (rounded down to the nearest integer)
        # print(max_population_row['population'], second_max_population_row['population'], most_populated_geoname_id, second_max_population_row['geonameid'])
        # quit()
        if not np.isinf(population_ratio) and not np.isnan(population_ratio):
            score = min(int(population_ratio), 10)  # Ensure the score doesn't exceed 10
        else:
            score = 0  # Default score if population_ratio is NaN

        increment_value = self.params.get_most_pop_value()
        if second_max_population_row['population'] == 0 and max_population_row['population'] != 0:
            score += increment_value
        # Update the score for the most populated place
        self.score_dict[most_populated_geoname_id] += score

    def country_similarity(self):
        target_toponym_set = set(self.candidate_rows_df['country_code'])
        # target_feature_code_set = set(target_rows['feature_code'])
        toponym_set = set(self.surrounding_toponyms)
        incr_value = self.params.get_sim_entity_value()

        for toponym in toponym_set:
            candidate_rows_df = pd.DataFrame(data[toponym])
            for country_code in target_toponym_set:
                if (candidate_rows_df['country_code'] == country_code).any():
                    geoname_id_list = list(self.candidate_rows_df[self.candidate_rows_df['country_code'] == country_code]['geonameid'])
                    for geo_id in geoname_id_list:
                        self.score_dict[geo_id] += incr_value
        return dict

    def superordinate_mention(self):
        target_toponym_set = set(self.candidate_rows_df['country_code'])
        # target_feature_code_set = set(target_rows['feature_code'])
        toponym_set = set(self.surrounding_toponyms)
        incr_value = self.params.get_superordinate_mention_value()

        for toponym in toponym_set:
            candidate_rows_df = pd.DataFrame(data[toponym])
            for country_code in target_toponym_set:
                filtered_rows_df = candidate_rows_df[
                    (candidate_rows_df['feature_code'] == 'PCLI') &
                    (candidate_rows_df['country_code'] == country_code)
                    ]

                if (filtered_rows_df['country_code'] == country_code).any():
                    geoname_id_list = list(self.candidate_rows_df[self.candidate_rows_df['country_code'] == country_code]['geonameid'])
                    for geo_id in geoname_id_list:
                        self.score_dict[geo_id] += incr_value

    def p_class_places(self):
        incr_value = self.params.get_pop_places_value()
        P_rows = self.candidate_rows_df[self.candidate_rows_df['feature_class'] == 'P']
        geoname_ids = P_rows['geonameid'].tolist()
        for geoname_id in geoname_ids:
            self.score_dict[geoname_id] += incr_value

    def feature_rank(self):
        pplc_value = self.params.get_pplc_value()
        PPLC_rows = self.candidate_rows_df[self.candidate_rows_df['feature_code'] == 'PPLC']
        geoname_ids = PPLC_rows['geonameid'].tolist()
        for geoname_id in geoname_ids:
            self.score_dict[geoname_id] += pplc_value

        pcli_value = self.params.get_plci_value()
        PCLI_rows = self.candidate_rows_df[self.candidate_rows_df['feature_code'] == 'PCLI']
        geoname_ids = PCLI_rows['geonameid'].tolist()
        for geoname_id in geoname_ids:
            self.score_dict[geoname_id] += pcli_value

        ppl_value = self.params.get_ppl_value()
        PPL_rows = self.candidate_rows_df[self.candidate_rows_df['feature_code'] == 'PPL']
        geoname_ids = PPL_rows['geonameid'].tolist()
        for geoname_id in geoname_ids:
            self.score_dict[geoname_id] += ppl_value
    def dutch_places(self):
        # Filter rows where country_code is 'nl' (Dutch)
        incr_value = self.params.get_dutch_places_value()
        dutch_rows = self.candidate_rows_df[self.candidate_rows_df['country_code'] == 'NL']
        dutch_geoname_ids = dutch_rows['geonameid'].tolist()
        for geoname_id in dutch_geoname_ids:
            self.score_dict[geoname_id] += incr_value

    def most_alt_names(self, geoname_id_list):
        greatest_name_count = 0
        greatest_geo_id = "not_found"
        for geo_id in geoname_id_list:
            rows = alt_df[self.alt_df['geonameid'].isin([geo_id])]
            row_count = rows.shape[0]
            if row_count > greatest_name_count:
                greatest_name_count = row_count
                greatest_geo_id = geo_id
        if greatest_geo_id == "not_found":
            return "no_alt_names"
        else:
            return greatest_geo_id

    def most_populated_place(self, geoname_id_list):
        rows = self.candidate_rows_df.loc[self.candidate_rows_df['geonameid'].isin(geoname_id_list)]
        # print(rows)
        # print(rows)
        rows['population'] = pd.to_numeric(rows['population'], errors='coerce')
        # print(rows['population'])
        max_population_row = rows.loc[rows['population'].idxmax()]
        #
        most_populated_geoname_id = max_population_row['geonameid']
        if max_population_row['population'] == 0:
            return "no_population"
        else:
            return most_populated_geoname_id

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


parser = argparse.ArgumentParser()
parser.add_argument("--maxpop", action="store_true", help="Perform georesolution with the maximum population as the sole heuristic")
parser.add_argument('--train', action='store_true', help="Run the algorithm on the train set")
parser.add_argument('--test', action='store_true', help="Run the algorithm on the test set")
parser.add_argument("--interactive", action="store_true", help="Prompt user for input")
parser.add_argument("--parameters", action="store_true", help="Prompt user for parameter weights. ")
args = parser.parse_args()
maxpop = args.maxpop
train = args.train
test = args.test
country_df = load_all_countries("filtered_all_countries.tsv")
alt_df = load_alt_names("filtered_alternative_names.tsv")
if args.interactive:
    user_text = unicodedata.normalize ('NFD',input("Enter a toponym: "))
    candidate_rows_df = pd.DataFrame(data[user_text])

    print("Candidate toponyms:")
    print(candidate_rows_df[["name", "geonameid", "population", "country_code", "feature_code"]])
    candidate_rows_df['population'] = pd.to_numeric(candidate_rows_df['population'], errors='coerce')
    # print(candidate_rows_df.loc[candidate_rows_df.nlargest(2, 'population').index[1]])
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

if args.parameters:
    parameters_obj = Parameters()
    vars_dict = vars(parameters_obj)
    for param in vars_dict:
        new_value = input(f"Enter a new value for {param} (default value: {vars_dict[param]}): ")
        if new_value == "":
            new_value = vars_dict[param]
        setattr(parameters_obj, param, new_value)

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
# parameters_obj = Parameters(pop_places=1.3, sim_entity=0, pplc_value=10, plci_value=100, ppl_value=0)
start_time = time.time()
with open('toponym_candidates.json') as json_file:
    data = json.load(json_file)

for file_id in text_toponym_dict:
    for entry in text_toponym_dict[file_id]:
        total_toponyms += 1
        target_toponym = entry[0]
        geoname_id = entry[1]
        surrounding_toponyms = get_surrounding_toponyms(text_toponym_dict[file_id], target_toponym)
        obj = GetCandidate(target_toponym, surrounding_toponyms, parameters_obj, alt_df)
        result_list = obj.get_most_likely_candidate(maxpop)
        most_likely_candidate_id = result_list[0]
        score_dict = "empty"
        if len (result_list) > 1:
            score_dict = result_list[1]
            # print(score_dict)
        if str(most_likely_candidate_id) != str(geoname_id):
            error_code = analyse_error(str(most_likely_candidate_id) , str(geoname_id), country_df)
            error_code = ""
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
                # print(target_toponym)
                unfound_toponyms += 1
            elif most_likely_candidate_id == "top candidates have equal scores":
                equal_scores += 1
                # if len(score_dict) < 4:
                #     print(score_dict)
                #     print(surrounding_toponyms)
                #     print(most_likely_candidate_id, geoname_id)
            elif most_likely_candidate_id == "population_status_unknown":
                no_pop_status += 1
            else:
                # print(target_toponym, "actual:", geoname_id, most_likely_candidate_id, score_dict , file_id)
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
        # if str(most_likely_candidate_id) != str(end_time = time.time()
        # elapsed_time = end_time - start_time
        #
        # print(elapsed_time)geoname_id) and most_likely_candidate_id != "toponym_not_found":
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


end_time = time.time()
elapsed_time = end_time - start_time
print(elapsed_time)

print(vars(parameters_obj))
print("Correctly guessed toponyms: {} out of {} total toponyms.".format(correctly_guessed, total_toponyms))

print("Unfound toponyms: {} were not found.".format(unfound_toponyms))
if maxpop:
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
