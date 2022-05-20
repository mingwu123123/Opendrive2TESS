import matplotlib.pyplot as plt
from lxml import etree
from commonroad.scenario.scenario import Scenario
from collections import defaultdict

from opendrive2lanelet.opendriveparser.elements.opendrive import OpenDrive
from opendrive2lanelet.network import Network
import csv

from opendrive2lanelet.opendriveparser.parser import parse_opendrive

from opendrive2tess.utils import color_c


def convert_opendrive(opendrive: OpenDrive) -> Scenario:
    road_network = Network()
    road_network.load_opendrive(opendrive)
    # 在此处过滤车道类型
    # 精度 ParametricLaneGroup.to_lanelet(self, precision: float = 0.5)
    return road_network.export_commonroad_scenario(filter_types=["driving", "onRamp", "offRamp", "exit", "entry"])  # commonroad-io==2020.2 版本需要验证


def get_basic_info(opendrive, scenario):
    # 获取 link与交叉口关系
    road_junction = {}
    for road in opendrive.roads:
        road_junction[road.id] = road.junction and road.junction.id  # 此道路是在交叉口内部
    # print([k for k,v in road_junction.items() if v])

    # 获取道路与路段关系
    lanes_info = defaultdict(dict)
    for lane in scenario.lanelet_network.lanelets:
        # 获取所在路段
        lane_name = lane.lane_name
        road_id = int(lane_name.split('.')[0])
        lanes_info[lane.lanelet_id] = {
            "road_id": road_id,
            "left": {
                "lane_id": lane.adj_left,
                "same_direction": lane.adj_left_same_direction,
            },
            "right": {
                "lane_id": lane.adj_right,
                "same_direction": lane.adj_right_same_direction,
            },
            "predecessor_ids": lane.predecessor,
            "successor_ids": lane.successor,
            "type": lane.type,
            "name": lane.lane_name,
            "center_vertices": lane.center_vertices,
            "left_vertices": lane.left_vertices,
            "right_vertices": lane.right_vertices,
        }

        # 车道ID，中心车道为1， 正t方向升序，负t方向降序(基本可理解为沿参考线左右，注意车道行驶方向的左右和参考线左右不一样)
        print(lane.lane_name.split('.')[2], lane.adj_left, lane.adj_right)
    # print(lane_road_map)
    return lanes_info, road_junction


def show_lanes(f1, f2, scenario, lanes_info, road_junction):
    # 写入文件
    writer1 = csv.writer(f1)
    writer1.writerow(["路段ID", "路段名称", "车道ID", "宽度(m)", "中心点序列", "左侧折点序列", "右侧折点序列"])

    writer2 = csv.writer(f2)
    writer2.writerow(["连接段ID", "起始路段ID", "起始车道ID", "目标路段ID", "目标车道ID", "中心点序列", "左侧折点序列", "右侧折点序列"])
    for lane in scenario.lanelet_network.lanelets:
        x_list = []
        y_list = []
        # 获取所在路段
        road_id = lanes_info[lane.lanelet_id]['road_id']
        lane_name = lanes_info[lane.lanelet_id]['name']

        for coo in lane.center_vertices:
            # 绘制中心线
            x_list.append(coo[0])
            y_list.append(coo[1])

        center_string = ' '.join(["({} {}) ".format(coo[0], coo[1]) for coo in lane.center_vertices])
        left_string = ' '.join(["({} {}) ".format(coo[0], coo[1]) for coo in lane.left_vertices])
        right_string = ' '.join(["({} {}) ".format(coo[0], coo[1]) for coo in lane.right_vertices])
        predecessor_ids = lane.predecessor
        successor_ids = lane.successor
        if road_junction.get(road_id) is None:  # 区分此路段是否属于 junction, 同时 正常车道也有前后
            color = next(color_c)
            writer1.writerow([road_id, lane_name, lane.lanelet_id, '', center_string, left_string, right_string])
        else:
            color = next(color_c)
            for successor_id in successor_ids:
                for predecessor_id in predecessor_ids:
                    writer2.writerow(
                        [road_id, lanes_info[successor_id]['road_id'], successor_id,
                         lanes_info[predecessor_id]['road_id'], predecessor_id,
                         center_string, left_string, right_string])
        index = len(x_list) // 2
        plt.plot(x_list[:index], y_list[:index], color='g', linestyle="", marker=".", linewidth=1)
        plt.plot(x_list[index:], y_list[index:], color='r', linestyle="", marker=".", linewidth=1)
    f1.close()
    f2.close()
    plt.show()


if __name__ == "__main__":
    xodr_file = "files/test1.xodr"

    with open(xodr_file, "r") as file_in:
        obj = etree.parse(file_in).getroot()
        opendrive = parse_opendrive(obj)


    # ps: 在 junction 里面也会有 lane_name
    # 这一步加载道路信息，比如参考线之类，但同时删除了过多的历史信息，需要手动调整源码
    scenario = convert_opendrive(opendrive)
    # 提取基础信息
    lanes_info, road_junction = get_basic_info(opendrive, scenario)


    f1 = open("files/车道.csv", 'w', newline='')
    f2 = open("files/车道连接.csv", 'w', newline='')

    # 获取道路详情并写入文件
    show_lanes(f1, f2, scenario, lanes_info, road_junction)

    # 输出为 xml文件 commroad格式, 需要更改 commonroad-io 版本
    # path = "test1.xml"
    # from opendrive2lanelet.io.extended_file_writer import ExtendedCommonRoadFileWriter
    # with open(path, "w") as fh:
    #     writer = ExtendedCommonRoadFileWriter(
    #         scenario,
    #         source="OpenDRIVE 2 Lanelet Converter",
    #     )
    #     writer.write_scenario_to_file_io(fh)
