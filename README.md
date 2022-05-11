# Opendrive2TESS
opendrive2lanelet 在导出时丢失了大量的原始信息，我们可以根据需要调整源代码，以保留我们需要的车道信息
在现有需求中，我们需要对 Network.export_lanelet_network 进行调整
在 lanelet = parametric_lane.to_lanelet() 后加上
lanelet.lane_name = parametric_lane.id_
lanelet.type = parametric_lane.type
即可

对于opendrive而言，路段仅有一条参考线描述，故对路段的边界信息，我们可以通过车道的行驶方向&相邻关系 解析路段信息
另外，暂未获取道路高程/超高程信息
