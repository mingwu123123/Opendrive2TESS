import csv
import collections
import json


file_path = "df_all.csv"
reader = csv.reader(open(file_path, 'r'))

header = next(reader)
print(header)
mapping = collections.defaultdict(dict)
for data in reader:
    id = int(data[1])
    timestamp = int(data[2])
    lon = float(data[4])
    lat = float(data[5])
    mapping[id][timestamp] = (lon, lat)
json.dump(mapping, open("id_timestamp.json", 'w'))


reader = csv.reader(open(file_path, 'r'))
header = next(reader)
mapping = collections.defaultdict(dict)
for data in reader:
    id = int(data[1])
    timestamp = int(data[2])
    lon = float(data[4])
    lat = float(data[5])
    mapping[timestamp][id] = (lon, lat)
json.dump(mapping, open("timestamp_id.json", 'w'))


