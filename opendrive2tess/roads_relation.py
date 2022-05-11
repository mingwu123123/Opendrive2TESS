from xml.dom.minidom import parse
from opendrive2tess.utils import get_Refline

import matplotlib.pyplot as plt


def get_roads_line(xodr):
    root = xodr.documentElement
    links = root.getElementsByTagName('road')

    roads = {}
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
        roads[road_id] = {
            "junction_id": junction_id,  # -1 为非junction，此道路是在交叉口内部
            'xy': xy_list,
            'length': road_length,
            # 高程/超高程信息暫未獲取
        } # 参考线信息
        for xy in xy_list:
            plt.plot([i[0] for i in xy], [i[1] for i in xy], color="r", linestyle="", marker=".")
        plt.show()

        if len(xy_list) > 1:
            print("此路段参考线由多条曲线组成")
    return roads

if __name__ == '__main__':
    xodr_file = "../test2.xodr"
    xodr = parse(xodr_file)

    roads = get_roads_line(xodr)
    # 绘制参考线
    for road_id, road_data in roads.items():
        road_xy_list = road_data['xy']
        for xy in road_xy_list:
            if road_data['junction_id'] == -1:
                color = 'g'
            else:
                color = 'r'
            plt.plot([i[0] for i in xy], [i[1] for i in xy], color=color, linestyle="", marker=".")
    plt.show()
