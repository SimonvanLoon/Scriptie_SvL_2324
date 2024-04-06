import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import os
import geocoder
from collections import Counter
import unicodedata

# Load the data
gold_df = pd.read_csv("annotations_gold.tsv", sep="\t", header=None,
                      names=["file_id", "toponym", "geoname_id", "in_title"])

file_id_to_toponyms = {}

# Iterate through each row in the DataFrame
for index, row in gold_df.iterrows():
    file_id = str(row["file_id"])
    toponym = unicodedata.normalize ('NFD',row["toponym"])
    geoname_id = str(row["geoname_id"])
    #print("@{0}@".format (toponym))
    # If the file_id is not already in the dictionary, create a new list
    if file_id not in file_id_to_toponyms:
        file_id_to_toponyms[file_id] = []

    # Append the toponym to the list for the corresponding file_id
    file_id_to_toponyms[file_id].append([toponym,geoname_id])




def count_toponym_occurrences_without_tokenizing(text, toponym):
    # Convert the entire text and the toponym to lowercase for case-insensitive matching
    text_lower = text.lower()
    toponym_lower = toponym.lower()

    # Initialize a counter for occurrences
    num_occurrences = 0

    # Search for the exact toponym within the text
    index = text_lower.find(toponym_lower)
    while index != -1:
        # Check if the found toponym is a standalone word (not part of a longer word)
        if (index == 0 or not text_lower[index - 1].isalpha()) and \
           (index + len(toponym_lower) == len(text_lower) or not text_lower[index + len(toponym_lower)].isalpha()):
            num_occurrences += 1

        # Search for the next occurrence
        index = text_lower.find(toponym_lower, index + 1)

    return num_occurrences


# Now 'file_id_to_toponyms' contains the desired dictionary
# print(file_id_to_toponyms)

new_df = pd.DataFrame(columns=["file_id", "toponym", "geoname_id", "first_index_toponym", "last_index_toponym"])
set_1 = set()
directory_path = 'Files'  # Replace with your actual directory path
for filename in os.listdir(directory_path):
    if filename.endswith('.txt'):
        full_file_path = os.path.join(directory_path, filename)
        try:
            with open(full_file_path, 'r', encoding='utf-8') as file:
                file_contents = unicodedata.normalize ('NFD',file.read())
                file_id = str(filename.split("_")[1].split(".")[0])
                if file_id in file_id_to_toponyms:
                    remaining_text = ""
                    for entry in file_id_to_toponyms[file_id]:
                        toponym = entry[0]
                        geoname_id = entry[1]
                        if toponym not in file_contents:
                            print("@{0}@".format(toponym))
                            print(toponym, "!!!!!!!!!!!!!!!", file_id_to_toponyms[file_id], file_id, file_contents)
                            quit()
                        toponym_count = count_toponym_occurrences_without_tokenizing(file_contents, toponym)
                        if toponym_count != file_id_to_toponyms[file_id].count(toponym):
                            set_1.add(file_id)
                            #print(toponym, file_id_to_toponyms[file_id], file_id, toponym_count, "!!", file_id_to_toponyms[file_id].count(toponym))
                        if remaining_text == "":
                            first_index_toponym = file_contents.find(toponym)
                            last_index_toponym = first_index_toponym+len(toponym)
                            remaining_text = file_contents[last_index_toponym:]
                            #print(remaining_text)
                            #print("!!!!!!!!!!!!")
                            new_row = {
                                "file_id": file_id,
                                "toponym": toponym,
                                "geoname_id": geoname_id,
                                "first_index_toponym": first_index_toponym,
                                "last_index_toponym": last_index_toponym
                            }
                            new_df = new_df._append(new_row, ignore_index=True)
                        else:
                            first_index_toponym = remaining_text.find(toponym)
                            last_index_toponym = first_index_toponym + len(toponym)
                            remaining_text = remaining_text[last_index_toponym:]
                            #print(remaining_text)
                            #print("!!!!!!!!!!!!")
                            new_row = {
                                "file_id": file_id,
                                "toponym": toponym,
                                "geoname_id": geoname_id,
                                "first_index_toponym": first_index_toponym,
                                "last_index_toponym": last_index_toponym
                            }
                            new_df = new_df._append(new_row, ignore_index=True)


        except FileNotFoundError:
            print(f"File {filename} not found.")
#print(set_1)
#print(len(set_1))
print(new_df.head(5))
print(len(new_df))
print(len(gold_df))
