import collections
import time

import matplotlib.pyplot as plt
import csv

from xml.dom.minidom import parse
from opendrive2tess.utils import get_Refline, get_elevation, color_c


def get_roads_info(xodr, step_length):
    root = xodr.documentElement
    links = root.getElementsByTagName('road')
    sum_xy = []
    roads_info = dict()
    for road in links:
        # 多条路段
        road_id = int(road.getAttribute('id'))
        print(road_id)
        # if road_id != 2203:
        #     continue
        junction_id = int(road.getAttribute('junction'))

        plan_view = road.getElementsByTagName('planView')[0]  # 每条道路有且仅有一条参考线，参考线通常在道路中心，但也可能有侧向偏移。
        # 参考线可能由多段曲线拼接而成
        geometrys = plan_view.getElementsByTagName('geometry')
        # 获取参考线坐标式, 一般为多段线
        road_length, road_center_vertices, geometry_center_vertices = get_Refline(geometrys, step_length)

        # 车道信息
        lanes = road.getElementsByTagName('lanes')[0]  # 每条路段有且仅有一处lanes
        lane_sections = lanes.getElementsByTagName('laneSection')
        def default_section():
            return {
                'right': [],
                'left': [],
                'all': []
            }
        index = 0
        sections_mapping = collections.defaultdict(default_section)
        for lane_section in lane_sections:
            right = lane_section.getElementsByTagName('right')
            left = lane_section.getElementsByTagName('left')
            if right:
                sections_mapping[index]['right'] = [int(lane.getAttribute('id')) for lane in right[0].getElementsByTagName('lane')]
            if left:
                sections_mapping[index]['left'] = [int(lane.getAttribute('id')) for lane in left[0].getElementsByTagName('lane')]
            sections_mapping[index]['all'] = sections_mapping[index]['right'] + sections_mapping[index]['left']
            index += 1

        sum_xy += road_center_vertices

        # 获取高程信息
        elevationProfiles = road.getElementsByTagName('elevationProfile')
        if not elevationProfiles:
            start_high, end_high = 0, 0
        else:
            # 高程 和 section 是互相独立的
            elevations = elevationProfiles[0].getElementsByTagName('elevation')
            start_high, end_high = get_elevation(elevations, road_length)

        roads_info[road_id] = {
            "junction_id": junction_id,  # -1 为非junction，此道路是在交叉口内部
            'road_center_vertices': road_center_vertices,
            'geometry_center_vertices': geometry_center_vertices,  # 每个section 分开，方便微观处理
            'length': road_length,
            'start_high': start_high,
            'end_high': end_high,
            'lane_sections': sections_mapping,
            # 路段边界作用不大，TESS是固定的车道宽度
        }

    return roads_info


def show_roads(f1, f2, roads_info):
    writer1 = csv.writer(f1)
    writer1.writerow(["路段ID", "路段名称", "長度(m)", "中心点序列", "左侧折点序列", "右侧折点序列"])

    writer2 = csv.writer(f2)
    writer2.writerow(["连接段ID", "長度(m)", "中心点序列", "左侧折点序列", "右侧折点序列"])
    sum_xy = []
    for road_id, road_data in roads_info.items():
        xy = road_data['road_center_vertices']
        center_string = ' '.join(["({} {}) ".format(coo[0], coo[1]) for coo in road_data['road_center_vertices']])
        sum_xy += xy

        if road_data['junction_id'] == -1:  # 非路口
            color = 'r'
            writer1.writerow([road_id, '', road_data['length'], center_string, '', ''])
            plt.plot([i[0] for i in sum_xy], [i[1] for i in sum_xy], color=color, linestyle="", marker=".")
        else:
            color = 'g'
            writer2.writerow([road_id, road_data['length'], center_string, '', ''])
            plt.plot([i[0] for i in sum_xy], [i[1] for i in sum_xy], color=color, linestyle="", marker=".")
    plt.show()
    f1.close()
    f2.close()
    return sum_xy


if __name__ == '__main__':
    num = 4
    xodr_file = f"files/test{num}.xodr"
    xodr = parse(xodr_file)
    start_time = time.time()

    step_length = 0.5
    roads_info = get_roads_info(xodr, step_length)
    # 绘制参考线&寫入文件
    f1 = open(f"files/路段{num}.csv", 'w', newline='')
    f2 = open(f"files/连接段{num}.csv", 'w', newline='')
    show_roads(f1, f2, roads_info)
    end_time = time.time()
    print(end_time - start_time)

    import json
    with open(f'files/路段{num}.json', 'w') as f:
        json.dump(roads_info, f)
