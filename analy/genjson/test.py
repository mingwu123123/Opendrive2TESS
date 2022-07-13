import json


data = json.load(open("wanji/back/geojson_laneel_outlines_1603453072002.json", 'r'))
from pprint import pprint
from collections import defaultdict
# pprint(data)


lanes_info = defaultdict(dict)
temp_road_id = 0

for feature in data["features"]:
    properties = feature["properties"]
    lane_ids = properties['roadSegmentPeerLanesList']
    if len(set(lane_ids) & set(lanes_info.keys())) not in [0, len(lane_ids)]:
        print(1) # 确认这样建立同一路段的车道是否合理
    if not set(lane_ids) & set(lanes_info.keys()):
        for lane_id in lane_ids:
            lanes_info[lane_id]['road_id'] = temp_road_id
        temp_road_id += 1

    # 记录车道详情
    center = properties[""]

print(lanes_info)



