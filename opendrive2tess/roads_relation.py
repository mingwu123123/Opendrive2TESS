from xml.dom.minidom import parse
from opendrive2tess.utils import get_Refline

import matplotlib.pyplot as plt
import csv
from functools import reduce


def get_roads_info(xodr):
    root = xodr.documentElement
    links = root.getElementsByTagName('road')

    roads_info = dict()
    for road in links:
        # 多条路段
        road_id = int(road.getAttribute('id'))
        junction_id = int(road.getAttribute('junction'))

        # temp_link = road.getElementsByTagName('link')
        # link_successors = temp_link[0].getElementsByTagName('successor')
        # link_predecessors = temp_link[0].getElementsByTagName('predecessor')

        plan_view = road.getElementsByTagName('planView')[0]  # 每条道路有且仅有一条参考线，参考线通常在道路中心，但也可能有侧向偏移。
        # 参考线可能由多段曲线拼接而成
        geometry = plan_view.getElementsByTagName('geometry')
        # 获取参考线坐标式, 一般为多段线
        road_length, xy_list = get_Refline(geometry, 1)

        center_vertices = reduce(lambda i, j: i + j, xy_list)
        roads_info[road_id] = {
            "junction_id": junction_id,  # -1 为非junction，此道路是在交叉口内部
            'center_vertices': center_vertices,
            'length': road_length,
            # 高程/超高程信息暫未獲取
        }

        plt.plot([i[0] for i in center_vertices], [i[1] for i in center_vertices], color="r", linestyle="", marker=".")
        plt.show()

        if len(xy_list) > 1:
            print("此路段参考线由多条曲线组成")
    return roads_info


def show_roads(f1, f2, roads_info):
    writer1 = csv.writer(f1)
    writer1.writerow(["路段ID", "路段名称", "長度(m)", "中心点序列", "左侧折点序列", "右侧折点序列"])

    writer2 = csv.writer(f2)
    writer2.writerow(["连接段ID", "長度(m)", "中心点序列", "左侧折点序列", "右侧折点序列"])

    for road_id, road_data in roads_info.items():
        xy = road_data['center_vertices']

        if road_data['junction_id'] == -1:
            color = 'g'
            writer1.writerow([road_id, '', road_data['length'], road_data['center_vertices'], '', ''])
        else:
            color = 'r'
            writer1.writerow([road_id, road_data['length'], road_data['center_vertices'], '', ''])
        plt.plot([i[0] for i in xy], [i[1] for i in xy], color=color, linestyle="", marker=".")
    plt.show()


if __name__ == '__main__':
    xodr_file = "../test1.xodr"
    xodr = parse(xodr_file)

    roads_info = get_roads_info(xodr)
    # 绘制参考线&寫入文件
    f1 = open("路段.csv", 'w', newline='')
    f2 = open("连接段.csv", 'w', newline='')
    show_roads(f1, f2, roads_info)

