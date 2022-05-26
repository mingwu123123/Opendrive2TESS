import matplotlib.pyplot as plt
from lxml import etree
from commonroad.scenario.scenario import Scenario
from collections import defaultdict

from opendrive2lanelet.opendriveparser.elements.opendrive import OpenDrive
from opendrive2lanelet.network import Network
import csv

from opendrive2lanelet.opendriveparser.parser import parse_opendrive

from opendrive2tess.utils import color_c

#TODO 过滤，lane_name

def convert_opendrive(opendrive: OpenDrive) -> Scenario:
    road_network = Network()
    road_network.load_opendrive(opendrive)
    # TODO 在此处过滤车道类型
    # 精度 ParametricLaneGroup.to_lanelet(self, precision: float = 0.5)
    # default filter_types:["driving", "onRamp", "offRamp", "exit", "entry"]
    laneTypes = [
        "none",
        "driving",
        "stop",
        "shoulder",
        "biking",
        "sidewalk",
        "border",
        "restricted",
        "parking",
        "bidirectional",
        "median",
        "special1",
        "special2",
        "special3",
        "roadWorks",
        "tram",
        "rail",
        "entry",
        "exit",
        "offRamp",
        "onRamp",
    ]
    return road_network.export_commonroad_scenario(filter_types=laneTypes)  # commonroad-io==2020.2 版本需要验证


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
        ids = lane_name.split('.')
        # lane.lanelet_id 自定义的车道编号,取消转换后，指的就是原始编号
        lanes_info[lane.lanelet_id] = {
            "road_id": int(ids[0]),
            "section_id": int(ids[1]),
            "lane_id": int(ids[2]),
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
            "name": lane_name,  # road_id+lane_section+lane_id+-1
            "center_vertices": lane.center_vertices.tolist(),
            "left_vertices": lane.left_vertices.tolist(),
            "right_vertices": lane.right_vertices.tolist(),
        }

    # 车道ID，中心车道为0， 正t方向升序，负t方向降序(基本可理解为沿参考线从左向右下降)
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
        # print(road_id, lanes_info[lane.lanelet_id]['type'], lanes_info[lane.lanelet_id]['name'])
        # if road_id not in [460]: # TODO 看他的上一个是什么，怎么连接
        #     continue
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
                    # 有可能车道的前置或者后续路段并不在此文件中，这种情况我们不记录<lanes_info[_id] 为{}， road_id 取''>
                    writer2.writerow(
                        [road_id, lanes_info[successor_id].get('road_id', ''), successor_id,
                         lanes_info[predecessor_id].get('road_id', ''), predecessor_id,
                         center_string, left_string, right_string])
        index = len(x_list) // 2
        plt.plot(x_list[:index], y_list[:index], color='g', linestyle="", marker=".", linewidth=1)
        plt.plot(x_list[index:], y_list[index:], color='r', linestyle="", marker=".", linewidth=1)
        # lan_id = int(lane.lane_name.split('.')[2])
        # if road_id != 2203:
        #     plt.plot(x_list, y_list, color='r', linestyle="", marker=".", linewidth=1)
        # else:
        #     plt.plot(x_list, y_list, color='g', linestyle="", marker=".", linewidth=1)
    f1.close()
    f2.close()
    plt.show()


if __name__ == "__main__":
    num = 4
    xodr_file = f"files/test{num}.xodr"

    with open(xodr_file, "r") as file_in:
        root_node = etree.parse(file_in).getroot()
        # 查找连接点
        for junction in root_node.findall("junction"):
            for connection in junction.findall("connection"):
                if connection.get("connectingRoad") == "460" and connection.get("incomingRoad") == "68":
                    print(connection.get("contactPoint"))
        opendrive = parse_opendrive(root_node)
                # newConnection.id = connection.get("id")
                # newConnection.incomingRoad = connection.get("incomingRoad")
                # newConnection.connectingRoad = connection.get("connectingRoad")
                # newConnection.contactPoint = connection.get("contactPoint")
                # if newConnection.connectingRoad == 460 and newConnection.incomingRoad == 68:
                #     print(1)

    # ps: 在 junction 里面也会有 lane_name
    # 这一步加载道路信息，比如参考线之类，但同时删除了过多的历史信息，需要手动调整源码
    scenario = convert_opendrive(opendrive)
    # 提取基础信息
    lanes_info, road_junction = get_basic_info(opendrive, scenario)


    f1 = open(f"files/车道{num}.csv", 'w', newline='')
    f2 = open(f"files/车道连接{num}.csv", 'w', newline='')

    # 获取道路详情并写入文件
    show_lanes(f1, f2, scenario, lanes_info, road_junction)
    import json
    with open(f'files/车道{num}.json', 'w') as f:
        json.dump(lanes_info, f)

    # 输出为 xml文件 commroad格式, 需要更改 commonroad-io 版本
    # path = "test1.xml"
    # from opendrive2lanelet.io.extended_file_writer import ExtendedCommonRoadFileWriter
    # with open(path, "w") as fh:
    #     writer = ExtendedCommonRoadFileWriter(
    #         scenario,
    #         source="OpenDRIVE 2 Lanelet Converter",
    #     )
    #     writer.write_scenario_to_file_io(fh)
