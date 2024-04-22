import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import pandas as pd
import unicodedata

def load_alt_names():
    gold_df = pd.read_csv('alternateNamesV2.txt', sep="\t", header=None, encoding='utf-8')
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
def load_all_countries():
    df = pd.read_csv('allCountries.txt', sep="\t", header=None, encoding='utf-8')
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


def load_annotations(filename):
    gold_df = pd.read_csv(filename, sep="\t", header=None,
                          names=["file_id", "toponym", "geoname_id", "in_title"])
    return gold_df

def create_toponym_set(gold_df):
    toponym_set = set()
    for index, row in gold_df.iterrows():
        toponym = unicodedata.normalize ('NFD',row["toponym"])
        toponym_set.add(toponym)
    return toponym_set

alternative_names_df = load_alt_names()
alternative_names_df['alternate name'].apply(
    lambda x: unicodedata.normalize('NFD', x) if isinstance(x, str) else x
)
all_countries_df = load_all_countries()
all_countries_df['name'].apply(
    lambda x: unicodedata.normalize('NFD', x) if isinstance(x, str) else x)
gold_df = load_annotations('annotations_gold.tsv')
toponym_set = create_toponym_set(gold_df)


filtered_alternative_names_df = alternative_names_df[alternative_names_df['alternate name'].isin(toponym_set)]

filtered_all_countries_df = all_countries_df[all_countries_df['name'].isin(toponym_set) |
                                              all_countries_df['geonameid'].isin(filtered_alternative_names_df['geonameid'])]


filtered_alternative_names_df.to_csv('filtered_alternative_names.tsv', sep='\t', index=False)


filtered_all_countries_df.to_csv('filtered_all_countries.tsv', sep='\t', index=False)