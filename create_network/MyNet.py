import collections

from PySide2.QtCore import *

from PySide2.QtWidgets import *
from Tessng import PyCustomerNet, TessInterface, TessPlugin, NetInterface, tngPlugin, tngIFace, m2p
from Tessng import NetItemType, GraphicsItemPropName
from basic_info.info import roads_info, lanes_info




class Road:
    def __init__(self, road_id, lane_ids=[]):
        self.id = road_id
        self._left_link = None
        self._right_link = None
        # section 仅有一个
        self.lane_ids = list(lane_ids)

    @property
    def left_link(self):
        return self._left_link

    @left_link.setter
    def left_link(self, obj):
        self._left_link = obj

    @property
    def right_link(self):
        return self._right_link

    @right_link.setter
    def right_link(self, obj):
        self._right_link = obj

    def tess_lane(self, lane_id):

        if lane_id > 0:
            tess_lanes = sorted(self.left_link.lanes(), key=lambda i: -i.number())
            return tess_lanes[lane_id - 1]
        else:
            tess_lanes = sorted(self.right_link.lanes(), key=lambda i: -i.number())
            return tess_lanes[abs(lane_id) - 1]

    def tess_link(self, lane_id):
        if lane_id > 0:
            return self.left_link
        else:
            return self.right_link


def get_coo_list(vertices):
    list1 = []
    for vertice in vertices:
        list1.append(QPointF(m2p(vertice[0] + 1700), m2p(vertice[1] - 2500)))
    return list1

# 用户插件子类，代表用户自定义与路网相关的实现逻辑，继承自MyCustomerNet
class MyNet(PyCustomerNet):
    def __init__(self):
        super(MyNet, self).__init__()

    # 创建路网
    def createNet(self):
        # 代表TESS NG的接口
        iface = tngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()


        link_mapping = dict()
        # 创建基础路段,数据原因，不考虑交叉口
        link_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] == -1]
        junction_road_ids = [road_id for road_id, road_info in roads_info.items() if road_info['junction_id'] != -1]
        # 创建所有的Link
        for road_id in link_road_ids:
            # if road_id != 626:
            #     continue
            for lane_id, lane_info in roads_info[road_id]['lanes'].items():
                print(lane_info['type'])

            lCenterLinePoint = get_coo_list(roads_info[road_id]['road_center_vertices'])
            #暂时只考虑一个section情况
            road_lane_info = list(filter(lambda i: i["road_id"] == int(road_id) and i["section_id"] == 0, lanes_info.values()))
            road_lane_info = sorted(road_lane_info, key=lambda i: i['lane_id'])  # 是否需要排序

            tess_road = Road(road_id, roads_info[road_id]["lanes"].keys())

            # 存在左车道
            if roads_info[road_id]['max_lane'] > 0:
                lCenterLinePoint = get_coo_list(roads_info[road_id]['road_center_vertices'][::-1])
                lanesWithPoints = [
                    {
                        'left': get_coo_list(lane_info['left_vertices']),
                        'center': get_coo_list(lane_info['center_vertices']),
                        'right': get_coo_list(lane_info['right_vertices']),
                    }
                    for lane_id, lane_info in roads_info[road_id]['lanes'].items() if lane_id > 0# and lane_info['type']=='driving'
                ]
                tess_road.left_link = netiface.createLinkWithLanePoints(lCenterLinePoint, lanesWithPoints)
                print(tess_road.left_link.id(), road_id)

            # 存在右车道
            if roads_info[road_id]['min_lane'] < 0:
                lCenterLinePoint = get_coo_list(roads_info[road_id]['road_center_vertices'])
                lanesWithPoints = [
                    {
                        'left': get_coo_list(lane_info['left_vertices']),
                        'center': get_coo_list(lane_info['center_vertices']),
                        'right': get_coo_list(lane_info['right_vertices']),
                    }
                    for lane_id, lane_info in roads_info[road_id]['lanes'].items() if lane_id < 0 #and lane_info['type']=='driving'
                ]
                tess_road.right_link = netiface.createLinkWithLanePoints(lCenterLinePoint, lanesWithPoints)
                print(tess_road.right_link.id(), road_id)
            link_mapping[road_id] = tess_road


        # # TODO 创建路段间的连接
        # for road_id in link_road_ids:
        #     # 如果前后车道都是路段，创建连接段
        #     for lane_id, lane_info in roads_info[road_id]["lanes"].items():
        #         lFromLaneNumber = []
        #         lToLaneNumber = []
        #         lanesWithPoints3 = []
        #         # if lane_info['type'] != 'driving':
        #         #     continue
        #         for predecessor_id in lane_info['predecessor_ids']:
        #             from_road_id = int(predecessor_id.split('.')[0])  # 假设此车道的上下游均各属于属于同一路段同一方向
        #             from_lane_id = int(predecessor_id.split('.')[2])
        #             from_link = link_mapping[from_road_id].tess_link(from_lane_id)
        #             from_line = link_mapping[from_road_id].tess_lane(from_lane_id)
        #
        #             for successor_id in lane_info["successor_ids"]:
        #                 to_road_id = int(successor_id.split('.')[0])  # 假设此车道的上下游均各属于属于同一路段
        #                 to_lane_id = int(successor_id.split('.')[2])
        #                 to_link = link_mapping[to_road_id].tess_link(to_lane_id)
        #                 to_line = link_mapping[to_road_id].tess_lane(to_lane_id)
        #
        #
        #
        #                 lFromLaneNumber.append(to_line.number())
        #                 lToLaneNumber.append(link_mapping[to_road_id].tess_lane(to_lane_id).number())
        #



        # 创建所有的交叉口,交叉口本身不作为车道，直接生成连接段
        # 多条车道属于一个road
        def default_dict():
            return {
                'lFromLaneNumber': [],
                'lToLaneNumber': [],
                'lanesWithPoints3': [],
                'infos': [],
            }

        sum_xy = []
        connector_mapping = collections.defaultdict(default_dict)
        for road_id in junction_road_ids:
            # 获取路口的所有连接关系
            for lane_id, lane_info in roads_info[road_id]["lanes"].items():
                # if lane_info['type'] != 'driving':
                #     continue
                for predecessor_id in lane_info['predecessor_ids']:
                    from_road_id = int(predecessor_id.split('.')[0])
                    from_lane_id = int(predecessor_id.split('.')[2])
                    from_link = link_mapping[from_road_id].tess_link(from_lane_id)
                    from_lane = link_mapping[from_road_id].tess_lane(from_lane_id)

                    for successor_id in lane_info["successor_ids"]:
                        to_road_id = int(successor_id.split('.')[0])  # 假设此车道的上下游均各属于属于同一路段
                        to_lane_id = int(successor_id.split('.')[2])
                        to_link = link_mapping[to_road_id].tess_link(to_lane_id)
                        to_lane = link_mapping[to_road_id].tess_lane(to_lane_id)

                        if from_lane.number() != 0 and to_lane.number() != 0: #  and from_road_id == 235 and to_road_id == 237:
                            print(f"{from_link.id()}-{to_link.id()}", from_lane.number(), to_lane.number())
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lFromLaneNumber'].append(from_lane.number())
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lToLaneNumber'].append(to_lane.number())
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['lanesWithPoints3'].append(get_coo_list(lane_info['center_vertices']))  # 注意连接线
                            sum_xy.append(lane_info['center_vertices'])
                            connector_mapping[f"{from_link.id()}-{to_link.id()}"]['infos'].append(
                                {
                                    "predecessor_id": predecessor_id,
                                    "successor_id": successor_id,
                                }
                            )


        for link_id, link_info in connector_mapping.items():
            from_link_id = int(link_id.split('-')[0])
            to_link_id = int(link_id.split('-')[1])
            lFromLaneNumber = link_info['lFromLaneNumber']
            lToLaneNumber = link_info['lToLaneNumber']
            lanesWithPoints3 = link_info['lanesWithPoints3']
            netiface.createConnectorWithPoints(from_link_id, to_link_id,
                                               lFromLaneNumber, lToLaneNumber,
                                               lanesWithPoints3)
            # import matplotlib.pyplot as plt
            # x_list, y_list = [i[0] for i in lanesWithPoints3], [i[1] for i in lanesWithPoints3]
            # index = len(x_list) // 2
            # plt.plot(x_list[:index], y_list[:index], color='g', linestyle="", marker=".", linewidth=1)
            # plt.plot(x_list[index:], y_list[index:], color='r', linestyle="", marker=".", linewidth=1)


        print(connector_mapping)
        # # 创建连接段，自动计算断点
        # #connector2 = netiface.createConnector(link1.id(), link2.id(), lFromLaneNumber, lToLaneNumber)

    def afterLoadNet(self):
        # 代表TESS NG的接口
        iface = tngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()
        # 设置场景大小
        netiface.setSceneSize(1000, 1000)
        # 获取路段数
        count = netiface.linkCount()
        if(count == 0):
            self.createNet()

