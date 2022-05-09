from xml.dom.minidom import parse
from script.utils import  get_Refline

import matplotlib.pyplot as plt
xodr_file = "../test1.xodr"
xodr = parse(xodr_file)

root = xodr.documentElement
links = root.getElementsByTagName('road')
for road in links:
    # 多条路段
    link_id = int(road.getAttribute('id'))
    junction = int(road.getAttribute('junction'))

    temp_link = road.getElementsByTagName('link')
    link_successors = temp_link[0].getElementsByTagName('successor')
    link_predecessors = temp_link[0].getElementsByTagName('predecessor')

    plan_view = road.getElementsByTagName('planView')[0] #每条道路有且仅有一条参考线，参考线通常在道路中心，但也可能有侧向偏移。
    geometry = plan_view.getElementsByTagName('geometry') # 参考线可能由多段曲线拼接而成
    xy_list = get_Refline(geometry, 1) # 获取参考线坐标式
    for xy in xy_list:
        plt.plot([i[0] for i in xy], [i[1] for i in xy], color="r", linestyle="", marker=".")
    plt.show()
    if len(xy_list) > 1:
        print(xy_list)
