# 原函数版，无误差，但是容易失败
import numpy as np
from sympy import *

def get_next_xy(f, tan2, coordinate: list, step_length, F):
    x = Symbol('x')
    # if df is None:
    #     df = np.sqrt(diff(f, x)**2 + 1)
    start_x = coordinate[0]
    end_definite = F.evalf(subs={x:start_x}) + step_length

    x_list = solve([F-end_definite], [x], dict=True)
    # solve(diff((1 - exp(-x)) ** x, x), x)
    # from sympy import lambdify
    # from scipy.optimize import fsolve
    #
    # func_np = lambdify(x, F-end_definite, modules=['numpy'])
    # solution = fsolve(func_np, start_x)

    coordinate_tan2s = dict()
    for answer in x_list:
        x_coordinate = answer.get(x)
        y_coordinate = f.evalf(subs={x:x_coordinate})
        # print(x_coordinate, y_coordinate)
        temp_tan2 = np.arctan2(float(y_coordinate - coordinate[1]), float(x_coordinate - coordinate[0]))
        abs_tan2 = abs(temp_tan2 - tan2)
        # 取角度相差最小值，作为下一次的计算方向,因爲采用了arctan2所以避免了方向錯誤
        coordinate_tan2s[abs_tan2] = [x_coordinate, y_coordinate, temp_tan2]
    min_abs_tan2 = min(coordinate_tan2s.keys())
    return coordinate_tan2s[min_abs_tan2] # 返回坐标及角度（为防止曲线角度突然变化，返回角度不取真实导数，取两点之间的变化）


x = Symbol('x')
a = 0
b = 0
c = 0
d = 1
f = a + b * x + c * x ** 2 + d * x ** 3
_df = (diff(f, x)**2 + 1) ** 0.5
#原函数
print(_df)
F=integrate(_df,x)
print(F)

tan2 = 0 #-pi #( 角度转arctan2)
step_length = 2
x_coordinate, y_coordinate = [0, 0]
while True:
    x_coordinate, y_coordinate, tan2 = get_next_xy(f, tan2, [x_coordinate, y_coordinate], step_length, F)
    print(x_coordinate, y_coordinate, tan2)
    import time
    time.sleep(1)
