import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import spacy
from spacy.lang.nl.examples import sentences
from spacy.tokens import Span


nlp = spacy.load("nl_core_news_sm")
doc = nlp("Germany is further from Japan than Moscow, Japan, Friesland")



print(doc.ents)
for ent in doc.ents:
    print(ent)
