import collections
import json
import os

import matplotlib.pyplot as plt
import csv

from xml.dom.minidom import parse
from analy.utils import get_Refline, get_elevation, color_c, get_section_info


def get_roads_info(xodr, step_length):
    root = xodr.documentElement
    links = root.getElementsByTagName('road')
    roads_info = dict()
    for road in links:
        # 多条路段
        road_id = int(road.getAttribute('id'))
        road_name = road.getAttribute('name')
        # if road_name not in ["434029", "434031", "434033", "434034", '434030']:
        #     continue
        # print(road_id)

        junction_id = int(road.getAttribute('junction'))

        plan_view = road.getElementsByTagName('planView')[0]  # 每条道路有且仅有一条参考线，参考线通常在道路中心，但也可能有侧向偏移。
        # 参考线可能由多段曲线拼接而成
        geometrys = plan_view.getElementsByTagName('geometry')
        # 获取参考线坐标式, 一般为多段线
        road_length, road_center_vertices, geometry_center_vertices = get_Refline(geometrys, step_length)

        # 车道信息
        lanes = road.getElementsByTagName('lanes')[0]  # 每条路段有且仅有一处lanes
        lane_sections = lanes.getElementsByTagName('laneSection')
        sections_mapping = get_section_info(lane_sections)

        # 获取高程信息
        elevationProfiles = road.getElementsByTagName('elevationProfile')
        if not elevationProfiles:
            start_high, end_high = 0, 0
        else:
            # 高程 和 section 是互相独立的
            elevations = elevationProfiles[0].getElementsByTagName('elevation')
            start_high, end_high = get_elevation(elevations, road_length)

        roads_info[road_id] = {
            "name": road_name,
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


def write_roads(work_dir, file_name, roads_info, show):
    with open(os.path.join(work_dir, f"{file_name}-路段.json"), 'w') as f:
        json.dump(roads_info, f)

    f1 = open(os.path.join(work_dir, f"{file_name}-路段.csv"), 'w', newline='')
    f2 = open(os.path.join(work_dir, f"{file_name}-连接段.csv"), 'w', newline='')

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
            writer1.writerow([road_id, '', road_data['length'], center_string, '', ''])
            if show:
                color = 'r'
                plt.plot([i[0] for i in sum_xy], [i[1] for i in sum_xy], color=color, linestyle="", marker=".")
        else:
            writer2.writerow([road_id, road_data['length'], center_string, '', ''])
            if show:
                color = 'g'
                plt.plot([i[0] for i in sum_xy], [i[1] for i in sum_xy], color=color, linestyle="", marker=".")
    plt.show()
    f1.close()
    f2.close()
    return sum_xy


def main(work_dir, file_name, step_length=0.5, show=False):
    xodr_file = os.path.join(work_dir, f"{file_name}.xodr")
    xodr = parse(xodr_file)

    roads_info = get_roads_info(xodr, step_length)
    # 写入文件&绘制参考线
    write_roads(work_dir, file_name, roads_info, show)
    return roads_info


if __name__ == '__main__':
    work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genjson', 'genjson_files')
    file_name = "wanji_0701"
    main(work_dir, file_name, show=True)
