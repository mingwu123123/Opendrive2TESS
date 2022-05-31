import os
import json
import time

import matplotlib.pyplot as plt
from lxml import etree
from commonroad.scenario.scenario import Scenario
from collections import defaultdict

from opendrive2lanelet.opendriveparser.elements.opendrive import OpenDrive
from opendrive2lanelet.network import Network
import csv

from opendrive2lanelet.opendriveparser.parser import parse_opendrive
from matlab import zeros, linspace

from analy.utils import color_c, get_elevation, section_info


# TODO 注意对第三方包的修改 --> change_convert.py

def convert_opendrive(opendrive: OpenDrive, filter_types: list=None) -> Scenario:
    road_network = Network()
    road_network.load_opendrive(opendrive)
    # TODO 在此处过滤车道类型
    # 精度 ParametricLaneGroup.to_lanelet(self, precision: float = 0.5)
    # 如果不传参数，将采取默认的过滤值 ["driving", "onRamp", "offRamp", "exit", "entry"]
    return road_network.export_commonroad_scenario(filter_types=filter_types)  # commonroad-io==2020.2 版本需要验证


def get_basic_info(opendrive, scenario):
    # 获取 link与交叉口关系
    road_junction = {}
    for road in opendrive.roads:
        road_junction[road.id] = road.junction and road.junction.id  # 此道路是在交叉口内部

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
            'traffic_lights': list(lane.traffic_lights),
            'traffic_signs': list(lane.traffic_signs),
        }

    # 车道ID，中心车道为0， 正t方向升序，负t方向降序(基本可理解为沿参考线从左向右下降)
    return lanes_info, road_junction


def main(work_dir, file_name, step_length=0.5, filter_types=None, show=False, write_csv=False):  # step_length需要对第三方包进行修改
    xodr_file = os.path.join(work_dir, f"{file_name}.xodr")

    with open(xodr_file, "r") as file_in:
        root_node = etree.parse(file_in).getroot()
        opendrive = parse_opendrive(root_node)

    roads_info = {}
    for road in opendrive.roads:
        planView = road.planView  # 每条道路有且仅有一条参考线，参考线通常在道路中心，但也可能有侧向偏移。
        center_vertices = []
        angles = []
        road_length = planView.length
        steps = int(road_length // step_length + 1)
        lengths = linspace(0, road_length, steps + 1)
        for length in lengths:
            position, angle = planView.calc_geometry(length)
            center_vertices.append(list(position))
            angles.append(angle)

        start_elevation = road.elevationProfile.elevations[0][0]
        end_elevation = road.elevationProfile.elevations[-1][0]
        road_start_high = get_elevation(start_elevation.start_pos, start_elevation.polynomial_coefficients)  # start_pos==2
        road_end_high = get_elevation(road_length, end_elevation.polynomial_coefficients)

        sections_mapping = section_info(road.lanes.lane_sections, filter_types)
        # elevations [(e1),(e2),(e3)]  start_pos, road.elevationProfile.elevations[0][0].polynomial_coefficients
        roads_info[road.id] = {
            "name": road.name,
            "junction_id": road.junction and road.junction.id,  # -1 为非junction，此道路是在交叉口内部
            'road_center_vertices': center_vertices,
            # 'geometry_center_vertices': geometry_center_vertices,  # 每个section 分开，方便微观处理
            'length': road_length,
            'start_high': road_start_high,
            'end_high': road_end_high,
            'lane_sections': sections_mapping,
            # 路段边界作用不大，TESS是固定的车道宽度
        }

    return roads_info


if __name__ == "__main__":
    start_time = time.time()
    work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../files')
    file_name = "map_hz_kaifangroad"
    laneTypes = [
        "none",
        "driving",
        "stop",
        "shoulder",
        "biking",
        "sidewalk",  #允许行人在上面行走的道路.人行横道由道路附属设施定义，不属于道路属性
        "border",
        "restricted",
        "parking",  # 带泊车位的车道
        "median",  # 分隔带
        # "bidirectional",  # 现在文档上已经不存在这种类型
        # "special1",  # 这是第三方包的过滤条件，目前看来应该较为原始，需要更新 Lane.laneTypes
        # "special2",
        # "special3",
        # "roadWorks",
        # "tram",
        # "rail",
        "entry",
        "exit",
        "offRamp",
        "onRamp",

        'curb',  # 路缘石 这是新增的types
        'connectingRamp',  # 连接匝道
    ]
    roads_info = main(work_dir, file_name, filter_types=laneTypes, show=True, write_csv=False)
    with open(os.path.join(work_dir, f"{file_name}-路段.json"), 'w') as f:
        json.dump(roads_info, f)
    print(time.time() - start_time)
