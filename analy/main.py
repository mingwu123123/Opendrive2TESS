import os
import json

import xodr2csv
import roads_relation

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
    roads_info = roads_relation.main(work_dir, file_name, filter_types, step_length=step_length)
    header_info, lanes_info = xodr2csv.main(work_dir, file_name, filter_types, step_length)
    road_lane_info = {
        "header": header_info,
        "road": roads_info,
        "lane": lanes_info,
    }
    with open(os.path.join(work_dir, f"{file_name}.json"), 'w') as f:
        json.dump(road_lane_info, f)
