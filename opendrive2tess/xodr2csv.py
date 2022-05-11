import matplotlib.pyplot as plt
from lxml import etree
from commonroad.scenario.scenario import Scenario
from collections import defaultdict

from opendrive2lanelet.opendriveparser.elements.opendrive import OpenDrive
from opendrive2lanelet.network import Network
import csv

from opendrive2lanelet.opendriveparser.parser import parse_opendrive


def convert_opendrive(opendrive: OpenDrive) -> Scenario:
    road_network = Network()
    road_network.load_opendrive(opendrive)
    return road_network.export_commonroad_scenario()  # commonroad-io==2020.2 版本需要验证


def get_basic_info(opendrive, scenario):
    # 获取 link与交叉口关系
    road_junction = {}
    for road in opendrive.roads:
        road_junction[road.id] = road.junction and road.junction.id  # 此道路是在交叉口内部
    # print([k for k,v in road_junction.items() if v])

    # 获取道路与路段关系
    lane_road_map = {}
    for lane in scenario.lanelet_network.lanelets:
        # 获取所在路段
        lane_name = lane.lane_name
        road_id = int(lane_name.split('.')[0])
        lane_road_map[lane.lanelet_id] = road_id
    # print(lane_road_map)
    return lane_road_map, road_junction


def get_lanes(f1, f2, scenario):
    # 写入文件
    writer1 = csv.writer(f1)
    writer1.writerow(["路段ID", "路段名称", "车道ID", "宽度(m)", "中心点序列", "左侧折点序列", "右侧折点序列"])

    writer2 = csv.writer(f2)
    writer2.writerow(["连接段ID", "起始路段ID", "起始车道ID", "目标路段ID", "目标车道ID", "中心点序列", "左侧折点序列", "右侧折点序列"])

    lanes = defaultdict(list)
    for lane in scenario.lanelet_network.lanelets:
        x_list = []
        y_list = []
        # 获取所在路段
        # TODO 需要重写 Network.export_lanelet_network 方法
        # lanelet = parametric_lane.to_lanelet()
        # # 在这里添加 lanelet 的 原始信息
        # lanelet.lane_name = parametric_lane.id_
        # lanelet.type = parametric_lane.type
        lane_type = lane.type  # 道路类型
        lane_name = lane.lane_name
        # TODO 如果需要绘制路段坐标详情，需要保留道路的左右测关系
        road_id = lane_road_map[lane.lanelet_id]

        for coo in lane.center_vertices:
            # 绘制中心线
            x_list.append(coo[0])
            y_list.append(coo[1])
            lanes[lane.lanelet_id].append(list(coo))

        center_string = ' '.join(["({} {}) ".format(coo[0], coo[1]) for coo in lane.center_vertices])
        left_string = ' '.join(["({} {}) ".format(coo[0], coo[1]) for coo in lane.left_vertices])
        right_string = ' '.join(["({} {}) ".format(coo[0], coo[1]) for coo in lane.right_vertices])
        predecessor_ids = lane.predecessor
        successor_ids = lane.successor
        if road_junction.get(road_id):  # 区分此路段是否属于 junction, 同时 正常车道也有前后
            color = 'r'
            for successor_id in successor_ids:
                for predecessor_id in predecessor_ids:
                    writer2.writerow(
                        ['', lane_road_map[successor_id], successor_id, lane_road_map[predecessor_id], predecessor_id,
                         center_string, left_string, right_string])
        else:
            color = 'y'
            writer1.writerow([road_id, lane_name, lane.lanelet_id, '', center_string, left_string, right_string])
        plt.plot(x_list, y_list, color=color, linestyle="", marker=".", linewidth=1)

    plt.show()
    return lanes


if __name__ == "__main__":
    xodr_file = "../test2.xodr"

    with open(xodr_file, "r") as file_in:
        obj = etree.parse(file_in).getroot()
        opendrive = parse_opendrive(obj)
    # ps: 在 junction 里面也会有 lane_name
    scenario = convert_opendrive(opendrive)  # 这一步删除了过多的历史信息，需要手动更改源码

    # 提取基础信息
    lane_road_map, road_junction = get_basic_info(opendrive, scenario)

    f1 = open("车道.csv", 'w', newline='')
    f2 = open("车道连接.csv", 'w', newline='')

    # 获取道路详情并写入文件
    lanes_info = get_lanes(f1, f2, scenario)

    # 输出为 xml文件 commroad格式, 需要更改 commonroad-io 版本
    # path = "test1.xml"
    # from opendrive2lanelet.io.extended_file_writer import ExtendedCommonRoadFileWriter
    # with open(path, "w") as fh:
    #     writer = ExtendedCommonRoadFileWriter(
    #         scenario,
    #         source="OpenDRIVE 2 Lanelet Converter",
    #     )
    #     writer.write_scenario_to_file_io(fh)
