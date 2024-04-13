import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import CountVectorizer
import os
import unicodedata
import json

def get_geo_class(geoname_id, filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    for element in data:
        if element['features'][0]["properties"]['geonames_id'] == geoname_id:
            class_code = element['features'][0]['properties']['code']
    return class_code







# Load the DataFrame, skipping the first row if it's not headers
gold_df = pd.read_csv("annotations_gold_index.tsv", sep="\t", skiprows=1,
                     names=["file_id", "toponym", "geoname_id", "first_index_toponym", "last_index_toponym", "class_code"])

filename = 'geo_dict.json'
file_id_to_toponyms = {}



for index, row in gold_df.iterrows():
    file_id = str(row["file_id"])
    toponym = unicodedata.normalize ('NFD',row["toponym"])
    geoname_id = row["geoname_id"]
    first_index = int(row["first_index_toponym"])
    last_index = int(row["last_index_toponym"])
    class_code = row["class_code"]

    #If the file_id is not already in the dictionary, create a new list
    if file_id not in file_id_to_toponyms:
        file_id_to_toponyms[file_id] = []

    # Append the toponym to the list for the corresponding file_id
    file_id_to_toponyms[file_id].append([toponym,geoname_id, first_index, last_index, class_code])







file_count = 0
directory_path = 'Files'  # Replace with your actual directory path
for file in os.listdir(directory_path):
    if file.endswith('.txt'):
        file_count += 1
print(file_count)

train_index = int(0.8 * file_count)
file_index = 0
context_window = 5
while file_index < train_index:
    for filename in os.listdir(directory_path):
        if filename.endswith('.txt'):
            full_file_path = os.path.join(directory_path, filename)
            try:
                with open(full_file_path, 'r', encoding='utf-8') as file:
                    file_contents = unicodedata.normalize('NFD', file.read())
                    file_id = str(filename.split("_")[1].split(".")[0])
                    if file_id in file_id_to_toponyms:
                        for entry in file_id_to_toponyms[file_id]:
                            first_index = entry[2]
                            last_index = entry[3]
                            words_before_list = file_contents[:first_index].split(" ")
                            words_after_list = file_contents[last_index:].split(" ")
                            context_words = words_before_list[-context_window:] + words_after_list[:context_window]
                            if file_id == "190899":
                                print(words_after_list[:context_window], first_index, last_index)

            except FileNotFoundError:
                print(f"File {filename} not found.")
            file_index += 1


def function():
    train_feats = ["pakt van rijke zakenman op voor corruptie in", "heeft een van de rijkste mensen van het land opgepakt wegens", "omkoping in het Afrikaanse land" ]
    train_labels = ["COUNTRY", "COUNTRY", "CITY"]
    test_feats = ["pakt rijke zakenman op voor Afrikaanse in", "rijkste Afrikaanse wegens", "omkoping rijke zakenman]" ]
    vectorizer = CountVectorizer()
    one_hot_vector = vectorizer.fit_transform(train_feats).toarray()
    print(one_hot_vector)
    #X_train = vectorizer.fit_transform(train_feats)
    #X_test = vectorizer.transform(test_feats)
    #mnb = MultinomialNB()
    #classifier = mnb.fit(X_train, train_labels)
    #print(classifier.predict(X_test))