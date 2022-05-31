import json
import os
from functools import lru_cache
import collections
import matplotlib.pyplot as plt

from math import sin
from cmath import cos, pi
from matlab import zeros, linspace

import matplotlib.pyplot as plt
from lxml import etree
from commonroad.scenario.scenario import Scenario
from collections import defaultdict

from opendrive2lanelet.opendriveparser.elements.opendrive import OpenDrive
from opendrive2lanelet.network import Network
import csv

from opendrive2lanelet.opendriveparser.parser import parse_opendrive

from analy.utils import color_c


# TODO 注意对第三方包的修改 --> change_convert.py
def convert_opendrive(opendrive: OpenDrive, filter_types: list) -> Scenario:
    road_network = Network()
    road_network.load_opendrive(opendrive)
    # TODO 在此处过滤车道类型
    # 精度 ParametricLaneGroup.to_lanelet(self, precision: float = 0.5)
    # 如果不传参数，将采取默认的过滤值 ["driving", "onRamp", "offRamp", "exit", "entry"]
    return road_network.export_commonroad_scenario(filter_types=filter_types)  # commonroad-io==2020.2 版本需要验证


def calc_elevation(pos, elevations):
    # 获取相应的 elevation
    for e in elevations:
        if pos >= e.start_pos:
            elevation = e
    a, b, c, d = elevation.polynomial_coefficients
    ds = pos  # 计算长度
    high = a + b * ds + c * ds ** 2 + d * ds ** 3
    return high

def convert_lanes_info(opendrive, scenario):
    # 获取 link与交叉口关系
    road_junction = {}
    for road in opendrive.roads:
        road_junction[road.id] = road.junction and road.junction.id  # 此道路是在交叉口内部

    # 获取道路与路段关系
    lanes_info = defaultdict(dict)
    for lane in scenario.lanelet_network.lanelets:
        # 获取所在路段
        lane_name = lane.lanelet_id
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

def write_lanes(work_dir, file_name, scenario, lanes_info, road_junction):
    with open(os.path.join(work_dir, f'{file_name}-车道.json'), 'w') as f:
        json.dump(lanes_info, f)

    f1 = open(os.path.join(work_dir, f"{file_name}-车道.csv"), 'w', newline='')
    f2 = open(os.path.join(work_dir, f"{file_name}-车道连接.csv"), 'w', newline='')

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
            writer1.writerow([road_id, lane_name, lane.lanelet_id, '', center_string, left_string, right_string])
        else:
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

    f1.close()
    f2.close()
    plt.show()



def write_roads(work_dir, file_name, roads_info):
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
            color = 'r'
            plt.plot([i[0] for i in sum_xy], [i[1] for i in sum_xy], color=color, linestyle="", marker=".")
        else:
            writer2.writerow([road_id, road_data['length'], center_string, '', ''])
            color = 'g'
            plt.plot([i[0] for i in sum_xy], [i[1] for i in sum_xy], color=color, linestyle="", marker=".")
    plt.show()
    f1.close()
    f2.close()
    return sum_xy


def convert_roads_info(opendrive, filter_types, step_length=0.5):  # step_length需要对第三方包进行修改
    roads_info = {}
    for road in opendrive.roads:
        road_length = road.length
        planView = road.planView  # 每条道路有且仅有一条参考线，参考线通常在道路中心，但也可能有侧向偏移。
        road_points = {}
        # 为了适配tess，将road按照section切分为多个link
        for section in road.lanes.lane_sections:
            points = []
            section_id = section.idx
            section_length = section.length
            section_sPos = section.sPos
            section_ePos = section_sPos + section_length

            steps = int(section_length // step_length + 1)
            lengths = linspace(section_sPos, section_ePos, steps + 1)
            # 计算每一点的坐标和角度
            for length in lengths:
                position, angle = planView.calc_geometry(length)
                points.append(
                    {
                        "position": list(position),
                        'angle': angle,
                    }
                )
            road_points[section_id] = {
                "points": points,
                'sPos': section_sPos,
                'ePos': section_ePos,
            }

        # 计算每一段section 的高程信息
        # 获取高程分段列表
        elevations = [elevation[0] for elevation in road.elevationProfile.elevations]
        for section_id, section_info in road_points.items():
            sPos = section_info["sPos"]
            ePos = section_info["ePos"]
            section_info["start_high"] = calc_elevation(sPos, elevations)
            section_info["end_high"] = calc_elevation(ePos, elevations)


        sections_mapping = convert_section_info(road.lanes.lane_sections, filter_types)
        # elevations [(e1),(e2),(e3)]  start_pos, road.elevationProfile.elevations[0][0].polynomial_coefficients
        roads_info[road.id] = {
            "name": road.name,
            "junction_id": road.junction and road.junction.id,  # -1 为非junction，此道路是在交叉口内部
            'road_points': road_points,
            # 'geometry_center_vertices': geometry_center_vertices,  # 每个section 分开，方便微观处理
            'length': road_length,
            # 'start_high': road_start_high,
            # 'end_high': road_end_high,
            'lane_sections': sections_mapping,
            # 路段边界作用不大，TESS是固定的车道宽度
        }

    return roads_info


def lane_restrictions(lane):
    speed_info = []
    access_info = []
    for speed in lane.getElementsByTagName('speed'):
        speed_info.append(
            {
                "sOffset ": speed.getAttribute("sOffset"),
                "max": float(speed.getAttribute("max")),
                "unit": speed.getAttribute("unit"),
            }
        )
    for access in lane.getElementsByTagName('access'):
        access_info.append(
            {
                "sOffset ": access.getAttribute("sOffset"),
                "rule ": access.getAttribute("rule"),
                "restriction ": access.getAttribute("restriction"),
            }
        )
    return {
        "speeds": speed_info,
        'accesss': access_info,
    }


def convert_section_info(sections, filter_types):
    # 车道信息
    def default_section():
        return {
            'right': [],
            'center': [],
            'left': [],
            'all': [],
            'infos': {}
        }

    sections_mapping = collections.defaultdict(default_section)
    for section in sections:
        section_id = sections.index(section)
        for lane in section.allLanes:
            if filter_types is not None and lane.type not in filter_types:
                continue
            if lane.id == 0:
                direction = 'center'
            elif lane.id >= 0:
                direction = 'left'
            else:
                direction = 'right'
            sections_mapping[section_id][direction].append(lane.id)
            # sections_mapping[index]['infos'][lane.id] = get_lane_restrictions(lane)

        sections_mapping[section_id]['all'] = sections_mapping[section_id]['right'] + sections_mapping[section_id]['left'] + sections_mapping[section_id]['center']
    # 缺少限制数据
    return sections_mapping