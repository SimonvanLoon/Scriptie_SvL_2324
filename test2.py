import sys
sys.path.insert(0, 'c:\\users\\user\\pycharmprojects\\scriptie\\.venv\\lib\\site-packages')
import geocoder



g = geocoder.geonames('Groningen', key='simonvanloon', maxRows=10,)
print([(r.address, r.country) for r in g])
