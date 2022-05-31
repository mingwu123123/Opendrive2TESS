import os
import json
from pyproj import Proj
from numpy import sign

step_length = 0.5
show = True
work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genjson_files')
file_name = 'wanji_0701'

with open(os.path.join(work_dir, f"{file_name}.json"), 'r') as f:
    data = json.load(f)
header_info = data['header']
roads_info = data['road']
lanes_info = data['lane']
roads_info = {
    int(k): v for k, v in roads_info.items()
}


convert_obj = Proj(header_info['geo_reference'])  # use kwargs

for lane_name, lane_info in lanes_info.items():
    if not lane_info:  # 此车道只是文件中某车道的前置或者后置车道，仅仅被提及，是空信息，跳过
        continue
    road_id = lane_info['road_id']
    section_id = lane_info['section_id']
    lane_id = lane_info['lane_id']

    # 添加默认属性
    roads_info[road_id].setdefault('sections', {})
    roads_info[road_id]['sections'].setdefault(section_id, {})
    roads_info[road_id]['sections'][section_id].setdefault('lanes', {})
    roads_info[road_id]['sections'][section_id]["lanes"][lane_id] = lane_info

# def roads_info[road_id]['lane_sections'][str(section_id)]['all']
def section_lane_info(road_id, section_id, lane_id, lane_ids):
    left_lanes = []
    right_lanes = []
    if lane_id >0:
        for lane in lane_ids:
            if lane < lane_id:
                left_lanes.append(lane)
            elif lane > lane_id:
                right_lanes.append(lane)
    elif lane_id < 0:
        for lane in lane_ids:
            if lane < lane_id:
                right_lanes.append(lane)
            elif lane > lane_id:
                left_lanes.append(lane)

    leftLanesList = []
    rightLanesList = []
    leftOpposingLanesList = []
    rightOpposingLanesList = []

    for lane in left_lanes:
        if sign(lane) == sign(lane_id):
            leftLanesList.append(f"{road_id}.{section_id}.{lane}.-1")
        else:
            leftOpposingLanesList.append(f"{road_id}.{section_id}.{lane}.-1")
    for lane in right_lanes:
        if sign(lane) == sign(lane_id):
            rightLanesList.append(f"{road_id}.{section_id}.{lane}.-1")
        else:
            rightOpposingLanesList.append(f"{road_id}.{section_id}.{lane}.-1")
    return leftLanesList, rightLanesList, leftOpposingLanesList, rightOpposingLanesList


def get_geo_json_with_lane():
    geo_info = {
      "type": "FeatureCollection",
      "features": []
    }
    for lane_name, lane_info in lanes_info.items():
        if not lane_info:  # 此车道只是文件中某车道的前置或者后置车道，仅仅被提及，是空信息，跳过
            continue
        # lane_name = lane_info['name']
        fromLaneIdsList = lane_info['predecessor_ids']
        toLaneIdsList = lane_info['successor_ids']
        road_id = int(lane_name.split(".")[0])
        section_id = int(lane_name.split(".")[1])
        lane_id = int(lane_name.split(".")[2])

        # 道路面信息构建
        coordinates = lane_info['center_vertices'][:1] + lane_info['left_vertices'] + lane_info['center_vertices'][-1:] + lane_info['right_vertices'][::-1] + lane_info['center_vertices'][:1]
        x_coordinates = [i[0] for i in coordinates]
        y_coordinates = [i[1] for i in coordinates]
        new_x_coordinates, new_y_coordinates = convert_obj(x_coordinates, y_coordinates, inverse=True)
        new_coordinates = [list(i) for i in zip(new_x_coordinates, new_y_coordinates)]
        accesss = roads_info[road_id]['lane_sections'][str(section_id)]['infos'].get(str(lane_id), {}).get('accesss', [])
        speeds = roads_info[road_id]['lane_sections'][str(section_id)]['infos'].get(str(lane_id), {}).get('speeds', [])
        leftLanesList, rightLanesList, leftOpposingLanesList, rightOpposingLanesList = section_lane_info(road_id, section_id, lane_id, roads_info[road_id]['lane_sections'][str(section_id)]['all'])
        geo_info['features'].append(
            {
                'type': "Feature",
                'geometry': {
                    "type": 'Polygon',
                    'coordinates': [new_coordinates],  # 添加每个lane的面面坐标即可
                },
                'properties': {
                    'id': lane_name,
                    'fromLaneIdsList': fromLaneIdsList,
                    'toLaneIdsList': toLaneIdsList,
                    'leftLanesList': leftLanesList,
                    'rightLanesList': rightLanesList,
                    'leftOpposingLanesList': leftOpposingLanesList,
                    'rightOpposingLanesList': rightOpposingLanesList,
                    'type': lane_info['type'],
                    'restrictions': {
                        'allowedVehicleTypesList': [access['restriction'] for access in accesss if access['rule' == 'allow']],
                        'speedLimitValue': speeds and speeds[0].get('max'),
                        'speedLimitUnit': speeds and speeds[0].get('unit'),
                    }
                }
                # "properties": {
                #     "prop0": "value0",
                #     "prop1": {"this": "that"}
                # }
            }
        )
        # break
    return geo_info


def get_geo_json_with_road():
    geo_info = {
        'type': "FeatureCollection",
        'features': []
    }
    fromLaneIdsList = []
    toLaneIdsList = []
    for road_id, road_info in roads_info.items():
        road_name = int(road_info['name'])
        for section_id, section_info in road_info.get('sections', {}).items():
            for lane_id, lane_info in section_info.get('lanes', {}).items():
                for predecessor_id in lane_info['predecessor_ids']:
                    if lanes_info.get(predecessor_id):
                        predecessor_road_id = lanes_info[predecessor_id]['road_id']
                        fromLaneIdsList.append(int(roads_info[predecessor_road_id]['name']))

                for successor_id in lane_info['successor_ids']:
                    if lanes_info.get(successor_id):
                        successor_road_id = lanes_info[successor_id]['road_id']
                        toLaneIdsList.append(int(roads_info[successor_road_id]['name']))

        geo_info['features'].append(
            {
                'type': "Feature",
                'geometry': {
                    "type": 'Polygon',
                    'coordinates': [[]],
                },
                'properties': {
                    'id': road_name,
                    'fromLaneIdsList': list(set(fromLaneIdsList)),
                    'toLaneIdsList': list(set(toLaneIdsList)),
                }
            }
        )
    return geo_info

geo_info = get_geo_json_with_lane()
json.dump(geo_info, open(f'genjson_files/{file_name}-geo.json', 'w'))

