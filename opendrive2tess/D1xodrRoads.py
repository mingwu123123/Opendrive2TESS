#coding=utf-8
#Python2.7
import xml.dom.minidom
import math
import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib import animation
from socket import *
from time import ctime
import struct
import copy
from collections import defaultdict
from functools import reduce
import csv

class VPath: #车辆路径
    def __init__(self):
        self.oid = []
        self.did = []
        self.flow = []
        self.interval = 1e6
        self.last_time = 0

class Signal():
    def __init__(self):
        self.id             = 0
        # self.link           = None
        self.laneidx_lst    = []
        self.pos            = 0
        # self.subtype        = -1
        self.timing         = []

    @property
    def clength(self):
        return len(self.timing)

class Light:
    def __init__(self, light_id, light_pos):
        self.id = light_id
        self.color = 0
        self.remain_time = 0
        self.pos = light_pos

    def is_red(self):
        return self.color == 1

    def is_yellow(self):
        return self.color == 2

    def is_green(self):
        return self.color == 3

class Lane(object):
    def __init__(self):
        self.id             = -1
        self.link_id        = -1
        self.type           = 'driving'
        self.width          = []
        self.speed_limit    = -1
        self.llid           = 0
        self.rlid           = 0
        self.lmark          = 'dashed'
        self.rmark          = 'dashed'
        self.llane          = None
        self.rlane          = None
        self.in_lane_id_lst = []
        self.out_lane_id_lst= []
        self.out_lane_lst   = []
        self.in_lane_lst    = []
        self.xy             = []
        self.direct         = []
        self.add_length     = []
        self.ownner         = None
        self.light          = None
        self.cross_lst      = []
        self.index = -1

    @property
    def length(self):
        return self.add_length[-1]

    @property
    def index_id(self):
        return self.link_id * 100 + self.id

    def cut_lane(self, position, up_len, down_len):
        sub_lane = Lane()
        up_pos = position - up_len
        down_pos = position + down_len
        add_uppos = [i for i in self.add_length]
        add_uppos.append(up_pos)
        add_downpos = [i for i in self.add_length]
        add_downpos.append(down_pos)
        add_uppos.sort()
        add_downpos.sort()
        uppos_index = add_uppos.index(up_pos)
        downpos_index = add_downpos.index(down_pos)
        sub_lane.add_length = self.add_length[max(0, uppos_index-1):downpos_index] #position not in add_length, -1
        x = self.xy[0][max(0, uppos_index-1):downpos_index]
        y = self.xy[1][max(0, uppos_index-1):downpos_index]
        sub_lane.xy = [x,y]
        sub_lane.id = self.id
        sub_lane.link_id = self.link_id
        return sub_lane

    def set_ownner(self, link):
        self.ownner = link

    def add_inlane(self, lane):
        if lane not in self.in_lane_lst:
            self.in_lane_lst.append(lane)

    def add_outlane(self, lane):
        if lane not in self.out_lane_lst:
            self.out_lane_lst.append(lane)

    def has_light(self):
        return self.light is not None

    def has_cross_point(self):
        return self.cross_lst

    def add_cross(self, this_offset, cross_offset, cross_lane, point):
        for c in self.cross_lst:
            if c.cross_lane is cross_lane:
                return
        cp = Cross(this_offset, cross_offset, cross_lane, point)
        self.cross_lst.append(cp)

    def is_driving_lane(self):
        return self.type == 'driving'

    def is_conn(self):
        return self.ownner.junction_id != -1

    def x(self):
        return self.xy[0]

    def y(self):
        return self.xy[1]

class Cross():
    def __init__(self, self_offset, cross_offset, cross_lane, point):
        self.this_position = self_offset
        self.cross_position = cross_offset
        self.cross_lane = cross_lane
        self.point = point

class Link():
    def __init__(self):
        self.id             = -1
        self.junction_id    = -1
        self.lane_lst       = []
        self.in_link_lst    = []
        self.out_link_lst   = []

    def add_lane(self, lane):
        self.lane_lst.append(lane)

    def iter_lane(self):
        for l in self.lane_lst:
            yield l

    def add_inlink(self, link):
        if link not in self.in_link_lst:
            self.in_link_lst.append(link)

    def add_outlink(self, link):
        if link not in self.out_link_lst:
            self.out_link_lst.append(link)

# 根据车道中心线坐标计算行驶方向和线长度序列
def get_line_feature(xy):
    xy = np.array(xy)
    # n为中心点个数，2为x,y坐标值
    x_prior = xy[0][:-1]
    y_prior = xy[1][:-1]
    x_post = xy[0][1:]
    y_post = xy[1][1:]
    # 根据前后中心点坐标计算【行驶方向】
    dx = x_post - x_prior
    dy = y_post - y_prior
    direction = list(map(lambda d: d > 0 and d or d + 2 * np.pi, np.arctan2(dy, dx))) #沿x轴方向逆时针转过的角度

    length = np.sqrt(dx ** 2 + dy ** 2)
    for i in range(len(length) - 1):
        length[i + 1] += length[i]
    return direction, length.tolist()

class Graph:
    def __init__(self):
        self.link_map = {}
        self.lane_map = {}
        self.vehicles = {}
        self.light_map = {}
        self.intersection_map = {} #在shp中才有用，用于绘制交叉口边界
        self.path_map = {}
        self.replace_linkmap = {}
        self.replace_lanemap = {}

    def add_link(self, link):
        if link.id not in self.link_map:
            self.link_map[link.id] = link
        else:
            raise Exception("Link is existed ?")

    def add_light(self, light):
        if light.id not in self.light_map:
            self.light_map[light.id] = light
        else:
            raise Exception("Link is existed ?")

    def add_lane(self, lane):
        if lane.index_id not in self.lane_map.keys():
            self.lane_map[lane.index_id] = lane
        else:
            raise Exception("Link is existed ?")

    def get_lane_inbetween(self,lane1, lane2): #get the common lane which are the outlane2 of conn1 and the inlane2 of conn2
        for one1 in lane1.out_lane_id_lst:
            for one2 in lane2.in_lane_id_lst:
                if one1 == one2:
                    return self.get_lane(one1)

    def get_lane(self, lane_id):
        return self.lane_map[lane_id]

    def get_vehicles_in_link(self, link):
        if link is None:
            return []
        vehs = []
        for veh in self.vehicles.values():
            if veh.current_link.id == link.id:
                vehs.append(veh)
        return vehs

    def get_vehicles_in_front_link(self, link0, link1, link2):
        links = [link0, link1, link2]
        link_ids = []
        for link in links:
            if link is None:
                link_ids.append(None)
            else:
                link_ids.append(link.id)
        vehs0 = []
        vehs1 = []
        vehs2 = []
        for veh in self.vehicles.values():
            if veh.current_link.id in link_ids:
                link_index = link_ids.index(veh.current_link.id)
                if link_index == 0:
                    vehs0.append(veh)
                elif link_index == 1:
                    vehs1.append(veh)
                elif link_index == 2:
                    vehs2.append(veh)
        return vehs0, vehs1, vehs2

    def get_vehicles_in_lanes(self, llane, rlane):
        lvehs = []
        rvehs = []
        for veh in self.vehicles.values():
            if llane and veh.current_lane.index_id == llane.index_id:
                lvehs.append(veh)
            if rlane and veh.current_lane.index_id == rlane.index_id:
                rvehs.append(veh)
        return [lvehs, rvehs]

    def get_vehicles_in_lane(self, lane):
        if lane is None:
            return []
        vehs = []
        for veh in self.vehicles.values():
            if veh.current_lane.index_id == lane.index_id:
                vehs.append(veh)
        return vehs

    def build_topo(self):
        for link in self.link_map.values():
            lane_id_lst = [l.id for l in link.lane_lst]
            llane_id_lst = [l for l in lane_id_lst if l > 0]
            rlane_id_lst = [l for l in lane_id_lst if l < 0]
            for lane in link.iter_lane():
                lane.set_ownner(link)
                if lane.id in llane_id_lst:
                    if lane.id != min(llane_id_lst):
                        lane.llid = lane.id - 1
                    if lane.id != max(llane_id_lst):
                        lane.rlid = lane.id + 1
                elif lane.id in rlane_id_lst:
                    if lane.id != min(rlane_id_lst):
                        lane.rlid = lane.id - 1
                    if lane.id != max(rlane_id_lst):
                        lane.llid = lane.id + 1
                # self.add_lane(lane)
                # self.lane_map[lane.index_id] = lane #补充lane_map,暂时将lane_id设为唯一的 TODO:此时lane_map中的lane并非具备全部信息

        for link in self.link_map.values():
            for lane in link.iter_lane():
                lane.llane = self.lane_map.get(lane.link_id * 100 + lane.llid, None)
                lane.rlane = self.lane_map.get(lane.link_id * 100 + lane.rlid, None)
                for lid in lane.out_lane_id_lst:
                    outlane = self.lane_map.get(lid)
                    if outlane is not None:
                        lane.out_lane_lst.append(outlane)
                    else:
                        lane.out_lane_id_lst.remove(lid)
                for lid in lane.in_lane_id_lst:
                    inlane = self.lane_map.get(lid)
                    if inlane is not None:
                        lane.in_lane_lst.append(inlane)
                    else:
                        lane.in_lane_id_lst.remove(lid)
                # lane.out_lane_lst = [self.lane_map.get(lid) for lid in lane.out_lane_id_lst]
                # lane.in_lane_lst = [self.lane_map.get(lid) for lid in lane.in_lane_id_lst]

                for in_lane_id in lane.in_lane_id_lst:
                    inlane = self.lane_map.get(in_lane_id)
                    if inlane is not None:
                        if inlane.ownner is None:
                            continue
                        lane.add_inlane(inlane)
                        link.add_inlink(inlane.ownner)
                for out_lane_id in lane.out_lane_id_lst[::-1]:
                    outlane = self.lane_map.get(out_lane_id)
                    if outlane is not None:
                        if outlane.ownner is None: #TODO:某些道路为driving连接border导致border没有ownner
                            continue
                        lane.add_outlane(outlane)
                        link.add_outlink(outlane.ownner)
                    else:
                        lane_index = lane.out_lane_id_lst.index(out_lane_id)
                        lane.out_lane_id_lst.pop(lane_index)
                # self.lane_map[lane.index_id] = lane
                # self.link_map[lane.link_id] = link

        for light in self.light_map.values():
            for lane_idx in light.laneidx_lst:
                lane = self.lane_map[lane_idx]
                lane.light = Light(light.id, light.pos)

    def link_combine(self):  # 合并具有相同属性的link，便于换道处理，相同属性定义：车道数相同、车道上下游一一对应、link有上下游关系，非连接器
        link_pairs = []  # 所有可配对的link对
        for link1 in self.link_map.values():
            if link1.junction_id != -1:
                continue
            for link2 in self.link_map.values():
                if link1 == link2 or len(link1.lane_lst) != len(
                        link2.lane_lst) or link1.junction_id != link2.junction_id or link2.junction_id != -1 or link2 not in link1.out_link_lst:
                    continue
                lanes1 = link1.lane_lst
                lanes2 = link2.lane_lst
                lane_connect = 0
                for i in range(0, len(lanes1)):
                    if lanes2[i] in lanes1[i].out_lane_lst and len(
                            lanes1[i].out_lane_lst) == 1:  # link2是link1的下游
                        lane_connect += 1
                if lane_connect == len(lanes1):
                    link_pairs.append([link1, link2])

        link_series = self.pair2series(link_pairs, [])  # 所有可配对的link序列

        for link_set in link_series:
            out_link_lst = link_set[-1].out_link_lst  # 先把所有下游link/lane关系进行替换
            for outlink in out_link_lst:
                outlink.in_link_lst.remove(link_set[-1])
                outlink.add_inlink(link_set[0])
            for lane in link_set[-1].lane_lst:
                out_lane_lst = lane.out_lane_lst
                for outlane in out_lane_lst:
                    outlane.in_lane_lst.remove(lane)
                    lane_index = link_set[-1].lane_lst.index(lane)
                    outlane.in_lane_lst.append(link_set[0].lane_lst[lane_index])
                    outlane.in_lane_id_lst = [x.id for x in outlane.in_lane_lst]

            # 再把link_series中最后一段的outlink给第一段
            link_set[0].out_link_lst = link_set[-1].out_link_lst
            # 将所有link序列信息合并到第一个link上
            for lane in link_set[0].lane_lst:
                lane_index = link_set[0].lane_lst.index(lane)
                lane.out_lane_lst = link_set[-1].lane_lst[lane_index].out_lane_lst
                for link in link_set[1:]:
                    lane.xy[0] = lane.xy[0] + link.lane_lst[lane_index].xy[0][1:]
                    lane.xy[1] = lane.xy[1] + link.lane_lst[lane_index].xy[1][1:]
                [lane.direct, lane.add_length] = get_lane_feature(lane.xy)

        # 删除合并后的无用路段，存储link替换数据
        for link_set in link_series:
            for link in link_set[1:][::-1]:
                if link.id not in self.replace_linkmap.keys():
                    self.replace_linkmap[link.id] = link_set[0].id
                    lane_num = len(link.lane_lst)
                    for i in range(lane_num):
                        self.replace_lanemap[link.lane_lst[i].id] = link_set[0].lane_lst[i].id
                    self.link_map.pop(link.id)
                else:
                    pass  # raise Exception("Lane is existed ?")

    def pair2series(self, pairs, series):
        if len(pairs) == 1:
            series.append(pairs[0])
            return series
        link_pair1 = pairs[0]           #每次取第一个元素，如果有上游/下游link就补充上，并放回；如果均没有上下游link，放到series中作为单独的序列
        pair_count2 = 0
        pair_count0 = 0
        pair_append2 = []
        pair_append0 = []


        for link_pair2 in pairs[1:]:    #先查找下游link
            if link_pair1[-1] == link_pair2[0]:
                pair_count2 += 1
                pair_append2.append(pairs.index(link_pair2))
        if pair_count2 == 1:            #如果只有一个下游就合并到上游link上，删除pairs中的下游关系；如果没有或有多个，就不合并
            [link_pair1.append(x) for x in pairs[pair_append2[0]][1:]]
            pairs.pop(pair_append2[0])

        for link_pair0 in pairs[1:]:    #再查找上游link
            if link_pair1[0] == link_pair0[-1]:
                pair_count0 += 1
                pair_append0.append(pairs.index(link_pair0))
        if pair_count0 == 1:            #如果只有一个下游就合并到上游link上，删除pairs中的下游关系；如果没有或有多个，就不合并
            [pairs[pair_append0[0]].append(x) for x in link_pair1[1:]]
            pairs.remove(link_pair1)

        if pair_count0 != 1 and pair_count2 != 1:   #如果上下游均没有可合并的link，就提出来放到series中
            series.append(link_pair1)
            pairs.remove(link_pair1)

        if pairs:
            return self.pair2series(pairs, series)
        else:
            return series

    def build_cross(self):
        for lane in self.lane_map.values():
            print('lane id:', lane.id)
            if lane.is_driving_lane() and lane.is_conn():
                self.calc_lane_cross_point(lane)
        self.save_cross_point()

    def calc_lane_cross_point(self, lane):
        near_set = set()
        for l in self.lane_map.values():
            if l.is_driving_lane() and l.is_conn() and l is not lane:
                near_set.add(l)

        for cross_lane in near_set:
            if cross_lane.ownner.junction_id == lane.ownner.junction_id and \
                            cross_lane.in_lane_lst[0] is not lane.in_lane_lst[0] and cross_lane.out_lane_lst[0] is not lane.out_lane_lst[0]:
                calculated = 0
                for cross in lane.cross_lst:
                    if cross_lane is cross.cross_lane:
                        calculated = 1
                        break
                if not calculated:
                    self.calc_cross_point(lane, cross_lane)

    def calc_cross_point(self, la, lb):
        # skip start and end position
        nmd = []
        for n in range(1, len(la.x()) - 1):
            for m in range(1, len(lb.x()) - 1):
                d = (la.x()[n] - lb.x()[m]) ** 2 + (la.y()[n] - lb.y()[m]) ** 2
                nmd.append((n, m, d))
        res = reduce(lambda p1, p2: p1[2] < p2[2] and p1 or p2, nmd)
        if res[2] < 0.2:
            n, m = res[0], res[1]
            la_offset = la.add_length[n]
            lb_offset = lb.add_length[m]
            la.add_cross(la_offset, lb_offset, lb, (la.x()[n], la.y()[n]))
            lb.add_cross(lb_offset, la_offset, la, (la.x()[n], la.y()[n]))

    def load_cross_point(self, filename):
        for l in read_csv(filename):
            tid = int(l[0])
            cid = int(l[1])
            cp = float(l[2])
            tp = float(l[3])
            x = float(l[4])
            y = float(l[5])
            tlane = tid in self.lane_map and self.lane_map[tid]
            clane = cid in self.lane_map and self.lane_map[cid]
            if not tlane or not clane:
                continue
            tlane.add_cross(tp, cp, clane, (x,y))

    def save_cross_point(self):
        with open('lane_cross', 'w') as f:
            for lane in self.lane_map.values():
                if not lane.is_driving_lane or not lane.is_conn():
                    continue
                for cross in lane.cross_lst:
                    line = '%d,%d,%.5f,%.5f,%.5f,%.5f\n'%(lane.index_id, cross.cross_lane.index_id, cross.cross_position, cross.this_position, cross.point[0], cross.point[1])
                    f.write(line)

    def get_sub_lane_to_outlane(self, link, dest_lane_lst):
        ret_lanes = []
        all_lanes = list(link.iter_lane())
        for l in all_lanes:
            if len(set(l.out_lane_lst).intersection(dest_lane_lst)) > 0:
                ret_lanes.append(l)
        return ret_lanes

    def get_path(self, origin, destination):
        paths = []
        path = [origin]
        outlink_id_lst_pre = [origin]
        paths.append(path)
        path_length = 1 #路径包含link的最大数量
        while outlink_id_lst_pre and path_length < 20:
            nextlink_id_lst = outlink_id_lst_pre
            paths_new = []
            outlink_id_lst_pre=[]
            for link_id in nextlink_id_lst:
                outlink_id_lst = []
                nextlink = self.get_link(link_id)
                if not nextlink.out_link_lst:
                    continue
                else:
                    for ll in nextlink.out_link_lst:
                        if ll.id not in outlink_id_lst and ll.id != origin:  # 避免绕一圈
                            outlink_id_lst.append(ll.id)
                            outlink_id_lst_pre.append(ll.id)
                # for l in nextlink.lane_lst:
                #     for nextlane in l.out_lane_lst:
                #         if not nextlane:
                #             continue
                #         if nextlane.link_id not in outlink_id_lst and nextlane.link_id != origin: #避免绕一圈
                #             outlink_id_lst.append(nextlane.link_id)
                for path in paths:
                    if path[-1] == link_id:
                        for lid in outlink_id_lst:
                            if lid in path:
                                if path not in paths_new:
                                    paths_new.append(path)
                                continue
                            path_new = path + [lid]
                            if path_new not in paths_new:
                                paths_new.append(path_new)
            if paths_new:
                # paths_new = list(np.unique(paths_new))
                paths = paths_new
            # print('path length: ', path_length)
            path_length += 1

            for pathx in paths:
                if pathx[-1] == destination:
                    return pathx

        print('unavailabile OD: ', origin, '  to ', destination)
        raise Exception("No avilabile path ?")

    def find_path(self, origin, destination):
        for path in self.path_map.values():
            if path.oid == origin and path.did == destination:
                return path.path_id_lst

        raise Exception("Invalid path ?")

    def create_path(self, path_set): #生成graph.path_map
        for path in path_set:
            # print('path: ',path)
            if path[0] in self.replace_linkmap.keys():
                path[0] = self.replace_linkmap[path[0]]  #如果路段发生过替换就进行替换
            if path[1] in self.replace_linkmap.keys():
                path[1] = self.replace_linkmap[path[1]]  #如果路段发生过替换就进行替换
            self.add_path(path[0], path[1], path[2])

    def add_path(self, oid, did, flow):
        if oid not in self.path_map:
            path = VPath()
            self.path_map[oid * did] = path
            path.oid = oid
            path.did = did
            path.flow = flow
            path.interval = 3600.0 / flow
            path.path_id_lst = self.get_path(oid, did)
        else:
            raise Exception("Same path is existed ?")

    def update_veh(self, car): #更新路网动态信息：车辆、信号配时
        self.vehicles[car.id] = car

    def update_signal(self, sim_time):  # 更新路网动态信息：车辆、信号配时
        #更新信号灯
        for light in self.light_map.values():
            for lane_idx in light.laneidx_lst:
                lane = self.lane_map[lane_idx]
                sim_time = int(sim_time) % light.clength
                lane.light.color = light.timing[sim_time]
                color_index = defaultdict(list)
                for k, va in [(v, i) for i, v in enumerate(light.timing)]:
                    color_index[k].append(va)
                aa = [a - sim_time for a in color_index[lane.light.color]]
                indexs = aa.index(0)
                for i in range(indexs + 1, len(aa)):
                    if aa[i] - aa[i - 1] > 1:
                        break
                lane.light.remain_time = i - indexs

    def get_pos(self, x, y):
        if random.random() > 0.5:
            pp = 1
        else:
            pp = -1
        xytext=(x+(4+int(random.random()*10))*pp, y+(3+int(random.random()*10)*pp))
        return xytext

    def draw(self, ax):
        cnames = {'aliceblue': '#F0F8FF',
                  'antiquewhite': '#FAEBD7',
                  'aqua': '#00FFFF',
                  'aquamarine': '#7FFFD4',
                  'azure': '#F0FFFF',
                  'beige': '#F5F5DC',
                  'bisque': '#FFE4C4',
                  'black': '#000000',
                  'blanchedalmond': '#FFEBCD',
                  'blue': '#0000FF',
                  'blueviolet': '#8A2BE2',
                  'brown': '#A52A2A',
                  'burlywood': '#DEB887',
                  'cadetblue': '#5F9EA0',
                  'chartreuse': '#7FFF00',
                  'chocolate': '#D2691E',
                  'coral': '#FF7F50',
                  'cornflowerblue': '#6495ED',
                  'cornsilk': '#FFF8DC',
                  'crimson': '#DC143C',
                  'cyan': '#00FFFF',
                  'darkblue': '#00008B',
                  'darkcyan': '#008B8B',
                  'darkgoldenrod': '#B8860B',
                  'darkgray': '#A9A9A9',
                  'darkgreen': '#006400',
                  'darkkhaki': '#BDB76B',
                  'darkmagenta': '#8B008B',
                  'darkolivegreen': '#556B2F',
                  'darkorange': '#FF8C00',
                  'darkorchid': '#9932CC',
                  'darkred': '#8B0000',
                  'darksalmon': '#E9967A',
                  'darkseagreen': '#8FBC8F',
                  'darkslateblue': '#483D8B',
                  'darkslategray': '#2F4F4F',
                  'darkturquoise': '#00CED1',
                  'darkviolet': '#9400D3',
                  'deeppink': '#FF1493',
                  'deepskyblue': '#00BFFF',
                  'dimgray': '#696969',
                  'dodgerblue': '#1E90FF',
                  'firebrick': '#B22222',
                  'floralwhite': '#FFFAF0',
                  'forestgreen': '#228B22',
                  'fuchsia': '#FF00FF',
                  'gainsboro': '#DCDCDC',
                  'ghostwhite': '#F8F8FF',
                  'gold': '#FFD700',
                  'goldenrod': '#DAA520',
                  'gray': '#808080',
                  'green': '#008000',
                  'greenyellow': '#ADFF2F',
                  'honeydew': '#F0FFF0',
                  'hotpink': '#FF69B4',
                  'indianred': '#CD5C5C',
                  'indigo': '#4B0082',
                  'ivory': '#FFFFF0',
                  'khaki': '#F0E68C',
                  'lavender': '#E6E6FA',
                  'lavenderblush': '#FFF0F5',
                  'lawngreen': '#7CFC00',
                  'lemonchiffon': '#FFFACD',
                  'lightblue': '#ADD8E6',
                  'lightcoral': '#F08080',
                  'lightcyan': '#E0FFFF',
                  'lightgoldenrodyellow': '#FAFAD2',
                  'lightgreen': '#90EE90',
                  'lightgray': '#D3D3D3',
                  'lightpink': '#FFB6C1',
                  'lightsalmon': '#FFA07A',
                  'lightseagreen': '#20B2AA',
                  'lightskyblue': '#87CEFA',
                  'lightslategray': '#778899',
                  'lightsteelblue': '#B0C4DE',
                  'lightyellow': '#FFFFE0',
                  'lime': '#00FF00',
                  'limegreen': '#32CD32',
                  'linen': '#FAF0E6',
                  'magenta': '#FF00FF',
                  'maroon': '#800000',
                  'mediumaquamarine': '#66CDAA',
                  'mediumblue': '#0000CD',
                  'mediumorchid': '#BA55D3',
                  'mediumpurple': '#9370DB',
                  'mediumseagreen': '#3CB371',
                  'mediumslateblue': '#7B68EE',
                  'mediumspringgreen': '#00FA9A',
                  'mediumturquoise': '#48D1CC',
                  'mediumvioletred': '#C71585',
                  'midnightblue': '#191970',
                  'mintcream': '#F5FFFA',
                  'mistyrose': '#FFE4E1',
                  'moccasin': '#FFE4B5',
                  'navajowhite': '#FFDEAD',
                  'navy': '#000080',
                  'oldlace': '#FDF5E6',
                  'olive': '#808000',
                  'olivedrab': '#6B8E23',
                  'orange': '#FFA500',
                  'orangered': '#FF4500',
                  'orchid': '#DA70D6',
                  'palegoldenrod': '#EEE8AA',
                  'palegreen': '#98FB98',
                  'paleturquoise': '#AFEEEE',
                  'palevioletred': '#DB7093',
                  'papayawhip': '#FFEFD5',
                  'peachpuff': '#FFDAB9',
                  'peru': '#CD853F',
                  'pink': '#FFC0CB',
                  'plum': '#DDA0DD',
                  'powderblue': '#B0E0E6',
                  'purple': '#800080',
                  'red': '#FF0000',
                  'rosybrown': '#BC8F8F',
                  'royalblue': '#4169E1',
                  'saddlebrown': '#8B4513',
                  'salmon': '#FA8072',
                  'sandybrown': '#FAA460',
                  'seagreen': '#2E8B57',
                  'seashell': '#FFF5EE',
                  'sienna': '#A0522D',
                  'silver': '#C0C0C0',
                  'skyblue': '#87CEEB',
                  'slateblue': '#6A5ACD',
                  'slategray': '#708090',
                  'snow': '#FFFAFA',
                  'springgreen': '#00FF7F',
                  'steelblue': '#4682B4',
                  'tan': '#D2B48C',
                  'teal': '#008080',
                  'thistle': '#D8BFD8',
                  'tomato': '#FF6347',
                  'turquoise': '#40E0D0',
                  'violet': '#EE82EE',
                  'wheat': '#F5DEB3',
                  'white': '#FFFFFF',
                  'whitesmoke': '#F5F5F5',
                  'yellow': '#FFFF00',
                  'yellowgreen': '#9ACD32'}

        for intersection in self.intersection_map.values():
            if intersection.virtuallink_lst[0].id in self.world:
                ax.plot(intersection.xy[0], intersection.xy[1],linestyle='--',color='k')  # 画 intersection boundary
                for link in intersection.virtuallink_lst: # draw center line in intersection
                    line_color = random.choice(list(cnames))
                    for lane in link.iter_lane():
                        ax.plot(lane.xy[0], lane.xy[1], color = cnames[line_color])  # 画车道中心线
        for link in self.link_map.values():
            if link.id not in self.world:# or link.junction_id != -1:
                continue
            line_color = random.choice(list(cnames))
            for lane in link.iter_lane():
                ax.plot(lane.xy[0], lane.xy[1], color = cnames[line_color])#画车道中心线
                #
                # n = len(lane.xy[0])
                # midx = lane.xy[0][int(n / 2)]
                # midy = lane.xy[1][int(n / 2)]
                # xytext = self.get_pos(midx, midy)
                # plt.annotate(str(lane.id), xy=(midx, midy), xytext=xytext, arrowprops=dict(arrowstyle='->', connectionstyle='arc3'))

        # for link in self.link_map.values():
        #     for lane in link.iter_lane():
        #         plt.plot(lane.xy[0], lane.xy[1])#画车道中心线
                # if lane.has_light():#画信号灯
                #     # 1.圆半径
                #     r = 1.0
                #     # 2.圆心坐标
                #     a, b, _ = lanepos2_worldxy(lane, lane.light.pos)
                #     # 参数方程
                #     theta = np.arange(0, 2 * np.pi, 0.01)
                #     x = a + r * np.cos(theta)
                #     y = b + r * np.sin(theta)
                #     if lane.light.is_red():
                #         color = 'r'
                #     elif lane.light.is_yellow():
                #         color = 'y'
                #     elif lane.light.is_green():
                #         color = 'g'
                #     else:
                #         color = 'b'
                #     plt.plot(x, y, color)
                #
                #     # plt.annotate("light:" + str(lane.light.id), xy=(a, b), xytext=(a+5, b+5), \
                #     #              arrowprops=dict(facecolor="r", headlength=1, headwidth=3, width=2))

    def get_link(self, link_id):
        if link_id in self.link_map.keys():
            return self.link_map[link_id]
        else:
            return self.link_map[self.replace_linkmap[link_id]]

    def conn_lanes_of_nextlink(self, lane, link): #获取下一个link上与当前lane有连接的车道
        return [outlane for outlane in lane.out_lane_lst if outlane.ownner is link]

def get_rect(x, y, width, length, angle):
    rect = np.array([(0, width / 2.0), (0, -width / 2.0), (-length, -width / 2.0), (-length, width / 2.0), (0, width / 2.0)])
        # theta = (np.pi / 180.0) * angle
    theta = angle
    R = np.array([[np.cos(theta), np.sin(theta)],[-np.sin(theta), np.cos(theta)]])
    offset = np.array([x, y])
    transformed_rect = np.dot(rect, R) + offset
    return transformed_rect

def lanepos2_worldxy(lane, position):  # 根据车辆当前状态更新车辆x,y坐标信息 VTD
    if position > lane.length:
        print('pos is larger than lane length!')
        if position < lane.length + 0.5:
            position = lane.length
    temp_len = lane.add_length + [position]
    temp_len.sort()
    temp_rank = temp_len.index(position)
    if temp_rank >= len(lane.direct):
        # print('this is imposible')
        temp_rank -= 1
    heading = lane.direct[temp_rank]
    x = lane.xy[0][temp_rank] + np.cos(heading) * (position - lane.add_length[temp_rank])
    y = lane.xy[1][temp_rank] + np.sin(heading) * (position - lane.add_length[temp_rank])
    return [x, y, heading]

def load_signals(graph, xosc):
    #得到文档元素对象
    root = xosc.documentElement
    RoadNetwork = root.getElementsByTagName('RoadNetwork')
    signals = RoadNetwork[0].getElementsByTagName('Signals')
    Controllers = signals[0].getElementsByTagName('Controller')
    for Controller in Controllers:
        Phases = Controller.getElementsByTagName('Phase')
        for phase in Phases:
            time_length = int(phase.getAttribute('duration'))
            Lights = phase.getElementsByTagName('Signal')
            for light in Lights:
                light_id = int(light.getAttribute('name'))
                if light_id not in graph.light_map.keys():
                    new_light = Signal()
                    new_light.id = light_id
                else:
                    new_light = graph.light_map[light_id]
                temp_timing = new_light.timing
                light_state = light.getAttribute('state')
                temp_state = light_state.split(';', 2)
                if len(temp_state) == 3:
                    if temp_state[0] == 'true':
                        temp_timing.extend([1 for _ in range(time_length)])
                    elif temp_state[1] == 'true':
                        temp_timing.extend([2 for _ in range(time_length)])
                    elif temp_state[2] == 'true':
                        temp_timing.extend([3 for _ in range(time_length)])
                    else:
                        raise Exception("Signal no timing ?")
                elif len(temp_state) == 2:
                    if temp_state[0] == 'true':
                        temp_timing.extend([1 for _ in range(time_length)])
                    elif temp_state[1] == 'true':
                        temp_timing.extend([3 for _ in range(time_length)])
                    else:
                        raise Exception("Signal no timing ?")
                else:
                    raise Exception("Signal type number ?")
                graph.light_map[light_id] = new_light

def get_Refline(geometry):
    Rclinex = []
    Rcliney = []
    Rdirect = []
    Radd_length = []
    for Rline in geometry:
        step_length = 0.2  # TODO: # 以0.1m作为步长
        temp_Rclinex = []
        temp_Rcliney = []
        temp_Rlength = 0
        Rstartx = float(Rline.getAttribute('x'))
        Rstarty = float(Rline.getAttribute('y'))
        Rheading = float(Rline.getAttribute('hdg'))
        Rlength = float(Rline.getAttribute('length'))
        if Rlength < 1e-3:
            continue
        temp_Rclinex.append(Rstartx)
        temp_Rcliney.append(Rstarty)
        Rdirect.append(Rheading)
        Radd_length.append(float(Rline.getAttribute('s')))
        Rline_index = geometry.index(Rline)
        if Rline_index < len(geometry) - 1:
            nextRline = geometry[Rline_index + 1]
            nextx = float(nextRline.getAttribute('x'))
            nexty = float(nextRline.getAttribute('y'))
        if Rline.getElementsByTagName('line'): # TODO 直线情况下，是否可以直接取到终点
            while temp_Rlength + step_length < Rlength: # else 直接取终点
                temp_Rclinex.append(temp_Rclinex[-1] + step_length * math.cos(Rheading))
                temp_Rcliney.append(temp_Rcliney[-1] + step_length * math.sin(Rheading))
                temp_Rlength += step_length
                Rdirect.append(Rheading)
                Radd_length.append(Radd_length[-1] + step_length)
        elif Rline.getElementsByTagName('arc'): #恒定曲率的弧线
            close2nextp = 0
            arc = Rline.getElementsByTagName('arc')
            curvature = float(arc[0].getAttribute('curvature'))
            delta_alpha = step_length * curvature
            temp_heading = Rheading
            while temp_Rlength + step_length < Rlength:
                #######
                # 用于平滑弧线/螺旋线尾端的累积误差，用直线连接目标点
                if Rline_index < len(geometry) - 1:
                    dist2nextp = math.sqrt((temp_Rclinex[-1] - nextx) ** 2 + (temp_Rcliney[-1] - nexty) ** 2) # TODO 相当于直连了
                    # if dist2nextp < 0.2:
                    #     break
                    if dist2nextp < 1.0: # 小于步长
                        temp_heading = np.arctan2(nexty - temp_Rcliney[-1], nextx - temp_Rclinex[-1]) # TODO 这一步输入正切数组求角度
                        # if temp_heading < 0:
                        #     temp_heading += math.pi * 2
                        delta_alpha = 0
                        if close2nextp == 0: #恒成立
                            Rlength = temp_Rlength + dist2nextp
                            close2nextp = 1
                #######
                temp_Rclinex.append(temp_Rclinex[-1] + step_length * math.cos(temp_heading))
                temp_Rcliney.append(temp_Rcliney[-1] + step_length * math.sin(temp_heading))
                temp_Rlength += step_length
                Rdirect.append(temp_heading)
                Radd_length.append(Radd_length[-1] + step_length)
                temp_heading += delta_alpha #可以直接相加吗，delta_alpha = step_length * curvature，并不是微分
        elif Rline.getElementsByTagName('spiral'):  # TODO:连接处做了平滑处理:是由于车道宽度导致的不平滑 螺旋线或回旋曲线
            close2nextp = 0
            spiral = Rline.getElementsByTagName('spiral')
            curvStart = float(spiral[0].getAttribute('curvStart'))
            curvEnd = float(spiral[0].getAttribute('curvEnd'))
            temp_heading = Rheading
            while temp_Rlength + step_length < Rlength:
                curvature = (temp_Rlength + 0.5 * step_length) / Rlength * (curvEnd - curvStart) + curvStart
                delta_alpha = step_length * curvature
                if Rline_index < len(geometry) - 1:
                    dist2nextp = math.sqrt((temp_Rclinex[-1] - nextx) ** 2 + (temp_Rcliney[-1] - nexty) ** 2)
                    if dist2nextp < 1.0:
                        temp_heading = np.arctan2(nexty - temp_Rcliney[-1], nextx - temp_Rclinex[-1])
                        # if temp_heading < 0:
                        #     temp_heading += math.pi * 2
                        delta_alpha = 0
                        if close2nextp == 0:
                            Rlength = temp_Rlength + dist2nextp
                            close2nextp = 1
                temp_Rclinex.append(temp_Rclinex[-1] + step_length * math.cos(temp_heading))  # 以0.1m作为步长
                temp_Rcliney.append(temp_Rcliney[-1] + step_length * math.sin(temp_heading))

                temp_Rlength += step_length
                Rdirect.append(temp_heading)
                Radd_length.append(Radd_length[-1] + step_length)
                temp_heading += delta_alpha
        elif Rline.getElementsByTagName('poly3'):
            poly3 = Rline.getElementsByTagName('poly3')
            a = float(poly3[0].getAttribute('a'))
            b = float(poly3[0].getAttribute('b'))
            c = float(poly3[0].getAttribute('c'))
            d = float(poly3[0].getAttribute('d'))
            sum_index = Rlength // step_length
            start_x = Rstartx
            start_y = Rstarty
            for i in range(sum_index):
                
            pass
        elif Rline.getElementsByTagName('paramPoly3'):
            pass
        else:
            raise Exception("Unknown Geometry !!!")
        Rclinex = Rclinex + temp_Rclinex
        Rcliney = Rcliney + temp_Rcliney
    for i in range(1, len(Rclinex) - 1):
        if abs(Rcliney[i + 1] - Rcliney[i]) < 1e-6 and abs(Rclinex[i + 1] - Rclinex[i]) < 1e-6 and i > 0:  # 两个点很接近
            Rdirect[i] = Rdirect[i - 1]

    return Rclinex, Rcliney, Rdirect, Radd_length

def create_road(graph, xodr, ax):
    #得到文档元素对象
    root = xodr.documentElement
    links = root.getElementsByTagName('road')
    for road in links:
        new_link = Link()
        new_link0 = Link()
        new_link.id = int(road.getAttribute('id'))
        new_link0.id = -int(road.getAttribute('id'))
        junction = int(road.getAttribute('junction'))
        new_link.junction_id = junction
        new_link0.junction_id = junction
        temp_link = road.getElementsByTagName('link')
        link_successor_id = None
        link_successor = temp_link[0].getElementsByTagName('successor')
        if link_successor and link_successor[0].getAttribute('elementType') == "road":
            link_successor_id = int(link_successor[0].getAttribute('elementId'))
            # new_link.out_link_lst.append(link_successor_id)  #TODO:还未考虑多个上下游的情况：已考虑junction，找路口进行验证
        link_predecessor_id = None
        link_predecessor = temp_link[0].getElementsByTagName('predecessor')
        if link_predecessor and link_predecessor[0].getAttribute('elementType') == "road":
            link_predecessor_id = int(link_predecessor[0].getAttribute('elementId'))
            # new_link.in_link_lst.append(link_predecessor_id) #TODO:还未考虑多个上下游的情况：已考虑junction，找路口进行验证
        plan_view = road.getElementsByTagName('planView')
        geometry = plan_view[0].getElementsByTagName('geometry')
        [Rclinex, Rcliney, Rdirect, Radd_length] = get_Refline(geometry) # 获取参考线坐标点序列，这里也很重要，不需要导出吗，怎么输入
        elevationProfile = road.getElementsByTagName('elevationProfile') #TODO：暂时没有考虑高程
        temp_lanes = road.getElementsByTagName('lanes') # 车道信息 需要对其进行分段（laneSection），lanes 是否有多个
        laneSection = temp_lanes[0].getElementsByTagName('laneSection') #TODO：可能有多段section，看起来只取了一段信息
        lanes = laneSection[0].getElementsByTagName('lane')
        lane_border_list = {}
        lane_width_list = {}
        for lane in lanes:
            new_lane = Lane()
            new_lane.id = int(lane.getAttribute('id')) #为了区分不同车道的情况
            if new_lane.id >= 0: #lane id 只是区分左右车道，为什么做这种转换
                new_lane.link_id = new_link.id
            else:
                new_lane.link_id = new_link0.id
            if new_lane.index_id in graph.lane_map.keys():
                new_lane = graph.get_lane(new_lane.index_id)
            else:
                graph.add_lane(new_lane)
            new_lane.type = lane.getAttribute('type')
            width = lane.getElementsByTagName('width')
            if not width:
                continue #如果没有width这个标签说明为地面标线，不是车道
            for k in range(0, len(width)): # 同一车道会有多个width吗
                a = float(width[k].getAttribute('a'))
                b = float(width[k].getAttribute('b'))
                c = float(width[k].getAttribute('c'))
                d = float(width[k].getAttribute('d'))
                offset_pre = float(width[k].getAttribute('sOffset'))
                temp_alength = Radd_length + [offset_pre]
                temp_alength.sort()
                temp_index = temp_alength.index(offset_pre)
                roadMark = lane.getElementsByTagName('roadMark') #TODO：暂时没有考虑标线
                # m_width = float(roadMark[0].getAttribute('width'))
                temp_width = [a + b * (s - offset_pre) + c * (s - offset_pre) ** 2 + d * (s - offset_pre) ** 3 for s in Radd_length[temp_index:]]
                new_lane.width[temp_index:] = temp_width
            if new_lane.type != 'driving':
                # if len(lane_border_list) == 0:# 应该先计算中间车道的坐标点，再计算外侧车道
                #     Rclinex = [x + a * math.cos(h + np.sign(new_lane.id) * math.pi / 2.0) for (x, h) in zip(Rclinex, Rdirect)]
                #     Rcliney = [y + a * math.sin(h + np.sign(new_lane.id) * math.pi / 2.0) for (y, h) in zip(Rcliney, Rdirect)]
                lane_border_list[new_lane.id] = new_lane
                lane_width_list[new_lane.id] = new_lane.width
                continue
            lane_successor = lane.getElementsByTagName('successor')
            if lane_successor: # 绑定车道关系？
                lane_successor_id = int(lane_successor[0].getAttribute('id'))
                try:
                    link_successor_id0 = int(np.sign(lane_successor_id)) * link_successor_id # 0
                    suc_id = link_successor_id0 * 100 + lane_successor_id # 为什么
                    if suc_id in graph.lane_map.keys():
                        suc_lane = graph.get_lane(suc_id)
                    else:
                        suc_lane = Lane()
                        suc_lane.link_id = link_successor_id0
                        suc_lane.id = lane_successor_id
                        graph.add_lane(suc_lane)
                    if suc_id not in new_lane.out_lane_id_lst and new_lane.id < 0:
                        new_lane.out_lane_id_lst.append(suc_id) #目前lane_id_lst存的都是修正过的车道id
                    elif suc_id not in new_lane.in_lane_id_lst and new_lane.id > 0:
                        new_lane.in_lane_id_lst.append(suc_id)  # 目前lane_id_lst存的都是修正过的车道id
                    if new_lane.index_id not in suc_lane.in_lane_id_lst and new_lane.id < 0:
                        suc_lane.in_lane_id_lst.append(new_lane.index_id)
                    elif new_lane.index_id not in suc_lane.out_lane_id_lst and new_lane.id > 0:
                        suc_lane.out_lane_id_lst.append(new_lane.index_id)
                except:
                    pass
            lane_predecessor = lane.getElementsByTagName('predecessor')
            if lane_predecessor:
                lane_predecessor_id = int(lane_predecessor[0].getAttribute('id'))
                link_predecessor_id0 = int(np.sign(lane_predecessor_id)) * link_predecessor_id
                pre_id = link_predecessor_id0 * 100 + lane_predecessor_id
                if pre_id in graph.lane_map.keys():
                    pre_lane = graph.get_lane(pre_id)
                else:
                    pre_lane = Lane()
                    pre_lane.link_id = link_predecessor_id0
                    pre_lane.id = lane_predecessor_id
                    graph.add_lane(pre_lane)
                if pre_id not in new_lane.in_lane_id_lst and new_lane.id < 0:
                    new_lane.in_lane_id_lst.append(pre_id)
                elif pre_id not in new_lane.out_lane_id_lst and new_lane.id > 0:
                    new_lane.out_lane_id_lst.append(pre_id)
                if new_lane.index_id not in pre_lane.out_lane_id_lst and new_lane.id < 0:
                    pre_lane.out_lane_id_lst.append(new_lane.index_id)
                elif new_lane.index_id not in pre_lane.in_lane_id_lst and new_lane.id > 0:
                    pre_lane.in_lane_id_lst.append(new_lane.index_id)
            lane_border_list[new_lane.id] = new_lane
            lane_width_list[new_lane.id] = new_lane.width

        for lane_id, new_lane in sorted(lane_border_list.items()):
            if lane_id < 0:
                continue
            # if new_lane.type == 'driving' and new_lane.id == 1:
            #     Rclinex0 = Rclinex
            #     Rcliney0 = Rcliney
            # if new_lane.type != 'driving':
            #     Rclinex0 = [x + w * math.cos(h + np.sign(new_lane.id) * math.pi / 2.0) for (x, h, w) in zip(Rclinex, Rdirect, lane_width_list[lane_id])]
            #     Rcliney0 = [y + w * math.sin(h + np.sign(new_lane.id) * math.pi / 2.0) for (y, h, w) in zip(Rcliney, Rdirect, lane_width_list[lane_id])]
            if lane_id - 1 in lane_border_list.keys():
                clinex = [x + (w1 + w2) * 0.5 * math.cos(h + np.sign(new_lane.id) * math.pi / 2.0) for (x, h, w1, w2) in zip(lane_border_list[lane_id-1].xy[0], Rdirect, lane_width_list[lane_id], lane_width_list[lane_id-1])] #应该先计算中间车道的坐标点，再计算外侧车道
                cliney = [y + (w1 + w2) * 0.5 * math.sin(h + np.sign(new_lane.id) * math.pi / 2.0) for (y, h, w1, w2) in zip(lane_border_list[lane_id-1].xy[1], Rdirect, lane_width_list[lane_id], lane_width_list[lane_id-1])]
            else:
                clinex = [x +  w * 0.5 * math.cos(h + np.sign(new_lane.id) * math.pi / 2.0) for (x, h, w) in zip(Rclinex[::-1], Rdirect, lane_width_list[lane_id])]  # 应该先计算中间车道的坐标点，再计算外侧车道
                cliney = [y +  w * 0.5 * math.sin(h + np.sign(new_lane.id) * math.pi / 2.0) for (y, h, w) in zip(Rcliney[::-1], Rdirect, lane_width_list[lane_id])]
            new_lane.xy = [clinex, cliney]
            # new_lane.xy = [clinex[::-np.sign(new_lane.id)], cliney[::-np.sign(new_lane.id)]]  # 车道id为负的话，需要倒序xy坐标
            lane_border_list[new_lane.id] = new_lane
        for lane_id, new_lane in sorted(lane_border_list.items(), reverse=True):
            if lane_id > 0:
                continue
            # if new_lane.type == 'driving' and new_lane.id == -1:
            #     Rclinex1 = Rclinex
            #     Rcliney1 = Rcliney
            # if new_lane.type != 'driving':
            #     Rclinex1 = [x + w * math.cos(h + np.sign(new_lane.id) * math.pi / 2.0) for (x, h, w) in zip(Rclinex, Rdirect, lane_width_list[lane_id])]
            #     Rcliney1 = [y + w * math.sin(h + np.sign(new_lane.id) * math.pi / 2.0) for (y, h, w) in zip(Rcliney, Rdirect, lane_width_list[lane_id])]
            if lane_id + 1 in lane_border_list.keys(): #？？？
                clinex = [x + (w1 + w2) * 0.5 * math.cos(h + np.sign(new_lane.id) * math.pi / 2.0) for (x, h, w1, w2) in zip(lane_border_list[lane_id+1].xy[0], Rdirect, lane_width_list[lane_id], lane_width_list[lane_id+1])] #应该先计算中间车道的坐标点，再计算外侧车道
                cliney = [y + (w1 + w2) * 0.5 * math.sin(h + np.sign(new_lane.id) * math.pi / 2.0) for (y, h, w1, w2) in zip(lane_border_list[lane_id+1].xy[1], Rdirect, lane_width_list[lane_id], lane_width_list[lane_id+1])]
            else:
                clinex = [x + w * 0.5 * math.cos(h + np.sign(new_lane.id) * math.pi / 2.0) for (x, h, w) in zip(Rclinex, Rdirect, lane_width_list[lane_id])]  # 应该先计算中间车道的坐标点，再计算外侧车道
                cliney = [y + w * 0.5 * math.sin(h + np.sign(new_lane.id) * math.pi / 2.0) for (y, h, w) in zip(Rcliney, Rdirect, lane_width_list[lane_id])]
            # new_lane.xy = [clinex[::-np.sign(new_lane.id)], cliney[::-np.sign(new_lane.id)]]  # 车道id为负的话，需要倒序xy坐标
            new_lane.xy = [clinex, cliney]
            lane_border_list[new_lane.id] = new_lane # 此处已经生成了车道坐标序列

        for lane_id, new_lane in lane_border_list.items():
            [new_lane.direct, new_lane.add_length] = get_line_feature(new_lane.xy)
            avg_width = np.mean(new_lane.width)
            if avg_width < 1 or new_lane.type != 'driving':
                continue
            # new_lane.type = new_link.type
            if lane_id > 0:
                new_link.lane_lst.append(new_lane)
            else:
                new_link0.lane_lst.append(new_lane)

        if new_link.lane_lst:
            new_link.lane_lst.sort(key=lambda x: x.id, reverse=True)
            graph.add_link(new_link)
        if new_link0.lane_lst:
            new_link0.lane_lst.sort(key=lambda x: x.id, reverse=False)
            graph.add_link(new_link0)

        signals = road.getElementsByTagName('signals')
        signal_lst = signals[0].getElementsByTagName('signal')
        for signal in signal_lst:
            sign_id = int(signal.getAttribute('id'))
            if sign_id not in graph.light_map.keys(): #道路标志标线，非信号灯
                continue
            sign = graph.light_map[sign_id]
            sign.pos = float(signal.getAttribute('s'))
            sign.link = new_link
            try:
                valid = signal.getElementsByTagName('validity')
                slane_id = int(valid[0].getAttribute('fromLane'))
                elane_id = int(valid[0].getAttribute('toLane'))
                if slane_id and elane_id:
                    for lid in range(slane_id, elane_id + 1):
                        sign.laneidx_lst.append(sign.link.id * 100 + lid)
                else:
                    sign.laneidx_lst = [l.index_id for l in sign.link.lane_lst]
            except:
                sign.laneidx_lst = [l.index_id for l in sign.link.lane_lst]


    junctions = root.getElementsByTagName('junction')
    for junction in junctions: #路口的坐标序列如何生成，是否可以通过车道连接关系TESS生成
        junction_id = int(junction.getAttribute('id'))
        connections = junction.getElementsByTagName('connection')
        for connection in connections:
            incomingRoad_id = int(connection.getAttribute('incomingRoad'))
            connectingRoad_id = int(connection.getAttribute('connectingRoad'))
            laneLinks = connection.getElementsByTagName('laneLink')
            for laneLink in laneLinks:
                pre_id = int(laneLink.getAttribute('from'))
                suc_id = int(laneLink.getAttribute('to'))
                if pre_id > 0:
                    incomingRoad = graph.link_map[incomingRoad_id]
                else:
                    incomingRoad = graph.link_map[-incomingRoad_id] #link_map为什么要生成负的id，还是同一个
                for lane in incomingRoad.lane_lst:
                    if lane.id == pre_id:
                        new_id = connectingRoad_id * 100 + suc_id
                        if new_id not in lane.out_lane_id_lst:
                            lane.out_lane_id_lst.append(new_id)
                if suc_id > 0:
                    connectingRoad = graph.link_map[connectingRoad_id]
                else:
                    connectingRoad = graph.link_map[-connectingRoad_id]
                for lane in connectingRoad.lane_lst:
                    if lane.id == suc_id:
                        new_id = incomingRoad_id * 100 + pre_id
                        if new_id not in lane.in_lane_id_lst:
                            lane.in_lane_id_lst.append(incomingRoad_id * 100 + pre_id) #？？

    graph.build_topo()
    # graph.load_cross_point('lane_cross')
    # graph.build_cross()

    for link in graph.link_map.values():
        link.lane_lst.sort(key=lambda x: x.id, reverse=False)
        for lane in link.lane_lst:
            if isinstance(lane.width, list):
                lane.width = lane.width[0]


    for link in graph.link_map.values():
        if link.id > 0:
            link.lane_lst.sort(key=lambda x: x.id, reverse=False)
        else:
            link.lane_lst.sort(key=lambda x: x.id, reverse=True)
        for lane in link.lane_lst:
            lane.index = link.lane_lst.index(lane) + 1
        # for lane in link.lane_lst:
        #     if link.id > 0:
        #         lane.index = len(link.lane_lst) - link.lane_lst.index(lane)
        #     else:
        #         lane.index = link.lane_lst.index(lane) + 1

    # graph.link_combine()
    return graph

# 根据车道中心线坐标计算行驶方向和线长度序列
def get_lane_feature(xy): # 重复函数？
    xy = np.array(xy)
    # n为中心点个数，2为x,y坐标值
    x_prior = xy[0][:-1]
    y_prior = xy[1][:-1]
    x_post = xy[0][1:]
    y_post = xy[1][1:]
    # 根据前后中心点坐标计算【行驶方向】
    dx = x_post - x_prior
    dy = y_post - y_prior

    direction = list(map(lambda d: d > 0 and d or d + 2 * np.pi, np.arctan2(dy, dx)))

    length = np.sqrt(dx ** 2 + dy ** 2)
    length = length.tolist()
    for i in range(len(length) - 1):
        length[i + 1] += length[i]
    length.insert(0, 0)
    return direction, length

def read_csv(file_path):#从csv文件中读取数据
    file_path.encode('utf-8')
    file = open(file_path)
    file_reader = csv.reader(file)
    for line in file_reader:
        yield line

def detail_xy(xy): #将原车道中心线上少量的点加密为0.1m间隔的点 # 不再使用？？
    [direct, add_length] = get_lane_feature(xy)
    dist_interval = 0.1
    new_xy = [[], []]
    new_direct = []
    new_add_len = [0]
    temp_length = dist_interval
    for k in range(0, len(xy[0]) - 1):
        new_xy[0].append(xy[0][k])
        new_xy[1].append(xy[1][k])
        new_add_len.append(temp_length)
        new_direct.append(direct[k])
        while temp_length < add_length[k + 1]:
            temp_length += dist_interval
            new_xy[0].append(new_xy[0][-1] + dist_interval * math.cos(direct[k]))
            new_xy[1].append(new_xy[1][-1] + dist_interval * math.sin(direct[k]))
            new_add_len.append(temp_length)
            new_direct.append(direct[k])
    return [new_xy, new_direct, new_add_len]

def worldxy2_lanepos(world_x, world_y, current_link, flag, last_pos, last_lane):  # 根据车道以及距离中心线起点长度，计算该点的二维坐标和方向角  # 不再使用？？
    search_r = 5
    min_dist = 1
    rest_len = last_lane.length - last_pos
    bond_lanes = []
    if flag is True:
        temp_lanes = []
    else:
        temp_lanes = current_link.lane_lst
    for temp_lane in temp_lanes:
        temp_lane = temp_lane.cut_lane(last_pos, 0, search_r)
        bond_lanes.append(temp_lane)

    if rest_len < search_r - min_dist: #不加min_dists会导致当more_len很小,cut_lane的结果没有长度
        next_links = current_link.out_link_lst
        more_len = search_r - rest_len
        for next_link in next_links:
            for next_lane in next_link.lane_lst:
                add_lane = next_lane.cut_lane(0, 0, more_len)
                if not add_lane.add_length:
                    continue
                bond_lanes.append(add_lane)

    min_dists = []
    for lane in bond_lanes:
        dist = float('inf')
        coord_num = 0
        if lane.add_length[1] - lane.add_length[0] < 0.2:
            lane_xy = lane.xy
        else:
            [lane_xy, _, _] = detail_xy(lane.xy)
        # lane_xy = lane.xy
        try:
            pos = lane.add_length[0]
        except:
            a = 1
        min_pos = pos
        while coord_num < len(lane_xy[0])-1:
            dist_interval = math.sqrt((lane_xy[0][coord_num+1] - lane_xy[0][coord_num]) ** 2 + (lane_xy[1][coord_num+1] - lane_xy[1][coord_num]) ** 2)
            temp = (lane_xy[0][coord_num] - world_x) ** 2 + (lane_xy[1][coord_num] - world_y) ** 2
            if dist > temp:
                dist = temp
                min_pos = pos
            pos += dist_interval
            coord_num += 1
        min_dists.append([dist, min_pos])

    min_d = reduce(lambda p1, p2: p1[0] < p2[0] and p1 or p2, min_dists)
    lane_ind = min_dists.index(min_d)
    veh_lane = bond_lanes[lane_ind].index_id
    # if min_d[0] > 3.0:
    #     print('FATAL: the nearest lane is 2m faraway', world_x, world_y, veh_lane)
    veh_pos = min_dists[lane_ind][1]
    return [veh_lane, veh_pos]

def worldxy2_lanepos_long(world_x, world_y, current_link, flag):  # 根据车道以及距离中心线起点长度，计算该点的二维坐标和方向角
    if flag is True:
        bond_lanes = []
    else:
        bond_lanes = current_link.lane_lst
    next_links = current_link.out_link_lst
    for next_link in next_links:
        bond_lanes = bond_lanes + next_link.lane_lst

    min_dists = []
    for lane in bond_lanes:
        dist = float('inf')
        coord_num = 0
        lane_xy = detail_xy(lane.xy)
        pos = 0
        while coord_num < len(lane_xy[0])-1:
            dist_interval = math.sqrt((lane_xy[0][coord_num+1] - lane_xy[0][coord_num]) ** 2 + (lane_xy[1][coord_num+1] - lane_xy[1][coord_num]) ** 2)
            pos += dist_interval
            temp = (lane_xy[0][coord_num] - world_x) ** 2 + (lane_xy[1][coord_num] - world_y) ** 2
            if dist > temp:
                dist = temp
                min_pos = pos
            coord_num += 1
        min_dists.append([dist, min_pos])
    min_d = reduce(lambda p1, p2: p1[0] < p2[0] and p1 or p2, min_dists)
    lane_ind = min_dists.index(min_d)
    veh_lane = bond_lanes[lane_ind]
    # if min_d[0] > 3.0:
    #     print('FATAL: the nearest lane is 2m faraway', world_x, world_y, veh_lane)
    veh_pos = min_dists[lane_ind][1]
    return [veh_lane, veh_pos]


