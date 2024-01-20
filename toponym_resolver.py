import csv

with open("annotations_gold.tsv", encoding='utf-8') as fd:
    rd = csv.reader(fd, delimiter="\t", quotechar='"')
    NL_count = 0
    for row in rd:
        if row[1][0].isupper() == False:
            print(row)


