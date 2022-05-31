import os
import json

# import xodr2csv

from lxml import etree
from opendrive2lanelet.opendriveparser.parser import parse_opendrive

from opendrive_info.utils import convert_opendrive, convert_roads_info, write_lanes, convert_lanes_info, write_roads



def main(work_dir, file_name, filter_types, step_length=0.5, detail=False):  # step_length需要对第三方包进行修改
    xodr_file = os.path.join(work_dir, f"{file_name}.xodr")

    with open(xodr_file, "r") as file_in:
        root_node = etree.parse(file_in).getroot()
        opendrive = parse_opendrive(root_node)

    header_info = {
        "date": opendrive.header.date,
        "geo_reference": opendrive.header.geo_reference,
    }

    roads_info = convert_roads_info(opendrive, filter_types, step_length)
    # ps: 在 junction 里面也会有 lane_name
    # 这一步加载道路信息，比如参考线之类，但同时删除了过多的历史信息，需要手动调整源码
    # 车道信息借助第三方包解析
    scenario = convert_opendrive(opendrive, filter_types)
    lanes_info, road_junction = convert_lanes_info(opendrive, scenario)

    # 写入文件&绘制参考线
    if detail:
        write_lanes(work_dir, file_name, scenario, lanes_info, road_junction)
        write_roads(work_dir, file_name, roads_info)
    return header_info, roads_info, lanes_info


if __name__ == '__main__':
    step_length = 0.5
    detail = False
    # 定义静态文件及所处位置文件夹
    work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
    file_name = '第II类路网'
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

    filter_types = ['driving']
    # TODO 注意对第三方包的修改 --> change_convert.py
    header_info, roads_info, lanes_info = main(work_dir, file_name, filter_types, step_length=step_length)
    road_lane_info = {
        "header": header_info,
        "road": roads_info,
        "lane": lanes_info,
    }
    with open(os.path.join(work_dir, f"{file_name}.json"), 'w') as f:
        json.dump(road_lane_info, f)
