import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import spacy
import pandas as pd
import glob



# Load the tsv file with the gold standard toponyms
gold_df = pd.read_csv("annotations_gold.tsv", sep="\t", header=None, names=["file_id", "toponym", "geoname_id", "in_title"])


# Load the txt files into a dictionary with file_id as key and text as value
txt_files = glob.glob("Files/*.txt")
txt_dict = {}
for file in txt_files:
    file_id = int(file.split("_")[1].split(".")[0])
    if file_id == "256":
        print('yeaheaa')
    with open(file, "r", encoding='utf-8') as f:
        text = f.read()
    txt_dict[file_id] = text

# Load a SpaCy model for your language
nlp = spacy.load("nl_core_news_lg")

# Process each txt file with SpaCy and extract the toponyms
spacy_toponyms = {}
for file_id, text in txt_dict.items():
    doc = nlp(text)
    toponyms = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    spacy_toponyms[file_id] = toponyms


# Create a dictionary from gold_df
gold_dict = gold_df.groupby('file_id')['toponym'].apply(list).to_dict()

# Loop through the dictionary

# Compare spacy_toponyms and gold_dict
for file_id in gold_dict.keys():
    spacy_set = set(spacy_toponyms[file_id])
    gold_set = set(gold_dict[file_id])
    if set(spacy_toponyms[file_id]) != set(gold_dict[file_id]):
        print(f"File ID: {file_id}")
        print("Spacy Toponyms: ", spacy_set)
        print("Gold Dictionary: ", gold_set)
        print("-" * 50)

# Compare the toponyms extracted by SpaCy with the gold standard toponyms
# You can use any metric you prefer, such as precision, recall, or F1-score
# Here we use a simple accuracy metric: the proportion of correct toponyms
# total = 0
# correct = 0
#
# for index, row in gold_df.iterrows():
#     file_id = row['file_id']
#     gold_set = set([row['toponym']])
#     if file_id in spacy_toponyms:
#         spacy_set = set(spacy_toponyms[file_id])
#     else:
#         spacy_set = set()
#
#     # Count the number of correct predictions
#     correct_predictions = gold_set & spacy_set
#     correct += len(correct_predictions)
#
#     # Count the total number of toponyms in the gold standard
#     total += len(gold_set)
#
# accuracy = correct / total if total > 0 else 0
# print(f"Accuracy: {accuracy}")
#
# # You can also use SpaCy's scorer module to evaluate the performance of the named entity recognizer
# # You need to convert your gold standard toponyms into SpaCy's annotation format
# # See https://spacy.io/usage/training#spacy-annotation for details
# gold_data = []
# for file_id, toponyms in gold_df.groupby("file_id")["toponym"]:
#     text = txt_dict[file_id]
#     entities = []
#     for toponym in toponyms:
#         start = text.find(toponym)
#         end = start + len(toponym)
#         entities.append((start, end, "GPE"))
#     gold_data.append((text, {"entities": entities}))
#
# # Use the scorer to evaluate the named entity recognizer on the gold data
# scorer = nlp.evaluate(gold_data)
# print(f"Precision: {scorer.ents_p}")
# print(f"Recall: {scorer.ents_r}")
# print(f"F1-score: {scorer.ents_f}")

import spacy
import classy_classification

# Load the spaCy model
nlp = spacy.load("en_core_web_md")

# Add the classy_classification pipe
nlp.add_pipe("classy_classification", config={
    "data": {
        "CITY": ["New York", "Milan", "London"]
    },
    "model": "spacy"
})

# Create the text and the list of items
text = "New York is lovely, Milan is nice, but London is amazing!"
items = ["New York", "Milan", "London"]

# Create a Doc object from the text
doc = nlp(text)

# Use the classy_classification pipe to classify the items
scores = [doc._.cats for item in items]

# Print the results
print(scores)
