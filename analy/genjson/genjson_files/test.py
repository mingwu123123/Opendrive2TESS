import json


data = json.load(open("back/geojson_laneel_outlines_1653551287476.json", 'r'))
from pprint import pprint



for i in data["features"]:
    print(i)
    if i ['properties']['id'] == 434633:
        pprint(i)