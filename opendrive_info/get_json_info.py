import collections
import json
import os
import time

from matlab import sqrt
def calc_width(l1, l2):
    width_list = []
    for index in range(len(l1)):
        width = sqrt((l1[index][0] - l2[index][0]) ** 2 + (l1[index][1] - l2[index][1]) ** 2)
        width_list.append(width)
    return width_list

work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')  # 下属必有files文件夹，用来存放xodr和生成的json/csv文件
file_name = 'map_hz_kaifangroad'

with open(os.path.join(work_dir, f"{file_name}.json"), 'r') as f:
    data = json.load(f)
header_info = data['header']
roads_info = data['road']
lanes_info = data['lane']
roads_info = {
    int(k): v for k, v in roads_info.items()
}
for road_id, road_info in roads_info.items():
    if road_info['junction_id'] == None:
        road_info['junction_id'] = -1


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

start_time = time.time()
for road_id, road_info in roads_info.items():
    for section_id, section_info in road_info['sections'].items():
        section_length = len(road_info['road_points'][str(section_id)]['lengths'])
        for lane_id, lane_info in section_info['lanes'].items():
            # 计算宽度
            lane_info['width'] = calc_width(lane_info['left_vertices'], lane_info['right_vertices'])
            # 确保车道点序列和参考线序列保持一致
            distance_length = len(lane_info['distance'])
            lane_length = len(lane_info['center_vertices'])
            if distance_length != section_length or distance_length != lane_length:
                print(1)

print(time.time() - start_time)
print(roads_info)