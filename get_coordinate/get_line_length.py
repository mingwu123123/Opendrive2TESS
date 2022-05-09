# 取点版
import numpy as np
from sympy import *
import matplotlib.pyplot as plt

def get_next_xy(f, tan2, coordinate: list, step_length):
    # if df is None:
    #     df = np.sqrt(diff(f, x)**2 + 1)
    start_x = coordinate[0]
    start_y = coordinate[1]
    # 根据象限确定下一点坐标
    if tan2 in [-pi, pi]:
        next_x = start_x - step_length
        next_y = start_y
    if tan2 == -pi / 2:
        next_x = start_x
        next_y = start_y - step_length
    elif tan2 == 0:
        next_x = start_x + step_length
        next_y = start_y
    elif tan2 == pi / 2:
        next_x = start_x
        next_y = start_y + step_length
    elif -pi < tan2 < -pi/2:
        next_x = start_x - step_length
        next_y = start_y - step_length
    elif -pi/2 < tan2 < 0:
        next_x = start_x + step_length
        next_y = start_y - step_length
    elif 0 < tan2 < pi/2:
        next_x = start_x + step_length
        next_y = start_y + step_length
    else:
        next_x = start_x - step_length
        next_y = start_y + step_length
    # 根据next_x
    coordinate_tan2s = dict()
    sum_list = []
    if next_x != start_x:
        sum_list += solve([f-y, x-next_x], [x, y], dict=True)
    if next_y != start_y:
        sum_list += solve([f-y, y-next_y], [x, y], dict=True)
    print(sum_list)
    # 加校验，此点在不在
    for temp in sum_list:
        print(temp)
        try:
            x_coordinate = float(temp[x])
            y_coordinate = float(temp[y])
            print(x_coordinate, y_coordinate)
        except:
            continue
        temp_tan2 = np.arctan2(float(y_coordinate - coordinate[1]), float(x_coordinate - coordinate[0]))
        print("temp_tan2: {}".format(temp_tan2))
        abs_tan2 = abs(temp_tan2 - tan2)
        # 取角度相差最小值，作为下一次的计算方向,因爲采用了arctan2所以避免了方向錯誤
        # TODO 取路径最小值更简单，但会不会出现方向错误
        coordinate_tan2s[abs_tan2] = [x_coordinate, y_coordinate, temp_tan2]
    if not coordinate_tan2s:
        print(11)
    print('end')
    min_abs_tan2 = min(coordinate_tan2s.keys())
    #积分长度大于length， 返回终点坐标
    return coordinate_tan2s[min_abs_tan2]  # 返回坐标及角度（为防止曲线角度突然变化，返回角度不取真实导数，取两点之间的变化）


x = Symbol('x')
y = Symbol('y')
a = 0
b = 1
c = 0
d = 1
f = a + b * x + c * x ** 2 + d * x ** 3
f = (100 - x ** 2) ** 0.5

tan2 = pi / 2 #-pi #( 角度转arctan2)
step_length = 2
x_coordinate, y_coordinate = [10, 0]
x_list, y_list = [], []
df = diff(f, x)

length = 20*pi - 10
sum_length = 0

x_list.append(x_coordinate)
y_list.append(y_coordinate)
while True:
    a,b = x_coordinate, y_coordinate
    x_coordinate, y_coordinate, tan2 = get_next_xy(f, tan2, [x_coordinate, y_coordinate], step_length)
    x_list.append(x_coordinate)
    y_list.append(y_coordinate)

    sum_length += float(abs(integrate((df**2 + 1) ** 0.5, (x, a, x_coordinate))))
    print(sum_length)
    if sum_length > length:
        break


plt.plot(x_list, y_list, color="r", linestyle="", marker=".", linewidth=0)
plt.show()

    # import time
    # time.sleep(1)
