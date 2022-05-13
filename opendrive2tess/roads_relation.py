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
        junction_id = int(road.getAttribute('junction'))

        # temp_link = road.getElementsByTagName('link')
        # link_successors = temp_link[0].getElementsByTagName('successor')
        # link_predecessors = temp_link[0].getElementsByTagName('predecessor')

        plan_view = road.getElementsByTagName('planView')[0]  # 每条道路有且仅有一条参考线，参考线通常在道路中心，但也可能有侧向偏移。
        # 参考线可能由多段曲线拼接而成
        geometrys = plan_view.getElementsByTagName('geometry')
        # 获取参考线坐标式, 一般为多段线
        road_length, center_vertices = get_Refline(geometrys, step_length)
        sum_xy += center_vertices

        # 获取高程信息
        elevationProfiles = road.getElementsByTagName('elevationProfile')
        if not elevationProfiles:
            start_high, end_high = 0, 0
        else:
            elevations = elevationProfiles[0].getElementsByTagName('elevation')
            start_high, end_high = get_elevation(elevations, road_length)

        roads_info[road_id] = {
            "junction_id": junction_id,  # -1 为非junction，此道路是在交叉口内部
            'center_vertices': center_vertices,
            'length': road_length,
            'start_high': start_high,
            'end_high': end_high,
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
        xy = road_data['center_vertices']
        center_string = ' '.join(["({} {}) ".format(coo[0], coo[1]) for coo in road_data['center_vertices']])
        sum_xy += xy

        if road_data['junction_id'] == -1:  # 非路口
            color = 'g'
            writer1.writerow([road_id, '', road_data['length'], center_string, '', ''])
        else:
            color = 'r'
            writer2.writerow([road_id, road_data['length'], center_string, '', ''])
        plt.plot([i[0] for i in sum_xy], [i[1] for i in sum_xy], color=next(color_c), linestyle="", marker=".")
    plt.show()
    f1.close()
    f2.close()


if __name__ == '__main__':
    xodr_file = "map_hz_kaifangroad.xodr"
    xodr = parse(xodr_file)

    step_length = 10
    roads_info = get_roads_info(xodr, step_length)
    # 绘制参考线&寫入文件
    f1 = open("路段.csv", 'w', newline='')
    f2 = open("连接段.csv", 'w', newline='')
    show_roads(f1, f2, roads_info)
