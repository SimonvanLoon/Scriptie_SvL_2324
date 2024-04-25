import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import unicodedata


def load_annotations(filename):
    gold_df = pd.read_csv(filename, sep="\t", header=None,
                          names=["file_id", "toponym", "geoname_id", "in_title"])
    return gold_df


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

def tuple_list_to_tsv(tuple_list, filename):
    new_df = pd.DataFrame(columns=["file_id", "toponym", "geoname_id", "in_title"])
    for fileid_toponyms in tuple_list:
        file_id = fileid_toponyms[0]
        for toponym_geoid in fileid_toponyms[1]:
            toponym = toponym_geoid[0]
            geoname_id = toponym_geoid[1]
            in_title = toponym_geoid[2]
            new_row = {
                "file_id": file_id,
                "toponym": toponym,
                "geoname_id": geoname_id,
                "in_title": in_title,
            }
            new_df = new_df._append(new_row, ignore_index=True)
    new_df.to_csv(filename, sep="\t", index=False, header=False)


gold_df = load_annotations('annotations_gold.tsv')
dict = create_dictionary(gold_df)
index = int(0.7 * len(dict))
key_value_list = [(key, value) for key, value in dict.items()]
train_list = key_value_list[:index]
test_list = key_value_list[index:]
tuple_list_to_tsv(train_list, "train_annotations.tsv")
tuple_list_to_tsv(test_list, "test_annotations.tsv")