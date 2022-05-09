from math import sin

from cmath import cos, pi
from matlab import *
import matplotlib.pyplot as plt


def Coordinate_rotation(X,Y,theta): #%X、Y是局部坐标值，theta对应于hdg角度,x、y全局坐标值。
    x=X*cos(theta)-Y*sin(theta)
    y=X*sin(theta)+Y*cos(theta)
    return x, y


def get_Refline(geometry, step_length):
    geometry_lines = dict()
    # geometry_id = 0
    # Rclinex = []
    # Rcliney = []
    # Rdirect = []
    # Radd_length = []
    init_xy = []
    road_length = 0
    for Rline in geometry:
        s=float(Rline.getAttribute('s'))
        x=float(Rline.getAttribute('x'))
        y=float(Rline.getAttribute('y'))
        hdg=float(Rline.getAttribute('hdg'))
        length=float(Rline.getAttribute('length'))
        steps = int(length // step_length + 1)

        road_length += length

        # temp_Rclinex = []
        # temp_Rcliney = []
        # temp_Rlength = 0
        # Rstartx = float(Rline.getAttribute('x'))
        # Rstarty = float(Rline.getAttribute('y'))
        # Rheading = float(Rline.getAttribute('hdg'))
        # Rlength = float(Rline.getAttribute('length'))
        # if Rlength < 1e-3:
        #     continue
        # temp_Rclinex.append(Rstartx)
        # temp_Rcliney.append(Rstarty)
        # Rdirect.append(Rheading)
        # Radd_length.append(float(Rline.getAttribute('s')))
        # Rline_index = geometry.index(Rline)
        # if Rline_index < len(geometry) - 1:
        #     nextRline = geometry[Rline_index + 1]
        #     nextx = float(nextRline.getAttribute('x'))
        #     nexty = float(nextRline.getAttribute('y'))
        if Rline.getElementsByTagName('line'):  # TODO 直线情况下，是否可以直接取到终点
            from sympy import cos, sin
            # 多段切割
            xy = zeros((steps, 2))
            for i in range(0, steps):
                xy[i][0] = x + (step_length * i) * cos(hdg)
                xy[i][1] = y + (step_length * i) * sin(hdg)

            # 起终点连接
            # xy = zeros((2, 2))
            # xy[0] = [x, y]
            # xy[1] = [x + length * cos(hdg), y + length * sin(hdg)]

            plt.plot([i[0] for i in xy], [i[1] for i in xy], color="r", linestyle="", marker=".")
            plt.show()
            print(xy)

        elif Rline.getElementsByTagName('arc'):  # 恒定曲率的弧线
            from matlab import sqrt, cos, pi, sin
            arc = Rline.getElementsByTagName('arc')[0]
            # x_arc=278 ;y_arc=-828;hdg_arc=0.50; s_arc=0 ;length_arc=34
            curvature = float(arc.getAttribute("curvature"))

            r = 1 / curvature  # 暂时不取绝对值
            xc = x - r * sin(hdg)  # TODO 圆心坐标（这种求法是否正确，可参照下方求点位的方法）
            yc = y + r * cos(hdg)
            print(xc, yc)  # 圆心
            theta = length / r  # 转动角度

            if curvature > 0:  # 逆时针旋转
                if -pi <= hdg < -pi / 2:  # 第三象限(-1/-0.5, 0.5/1)
                    angle_start = hdg + 1.5 * pi
                elif -pi / 2 <= hdg < 0:  # 第四象限(-0.5/0, -1/-0.5)
                    angle_start = hdg - 0.5 * pi
                elif 0 <= hdg < pi / 2:  # 第一象限(0/0.5, -0.5/0)
                    angle_start = hdg - 0.5 * pi
                else:  # 第二象限(0.5/1, 0/0.5)
                    angle_start = hdg - 0.5 * pi
            else:  # 顺时针旋转
                if -pi <= hdg < -pi / 2:  # 第三象限(-1/-0.5, -0.5/0)
                    angle_start = hdg + 0.5 * pi
                elif -pi / 2 <= hdg < 0:  # 第四象限(-0.5/0, 0/0.5)
                    angle_start = hdg + 0.5 * pi
                elif 0 <= hdg < pi / 2:  # 第一象限(0/0.5, 0.5/1)
                    angle_start = hdg + 0.5 * pi
                else:  # 第二象限(0.5/1, -1/-0.5)
                    angle_start = hdg - 1.5 * pi

            angle_start = float(angle_start)
            angle_end = float(angle_start + theta)  # TODO 需要考虑转多圈，累加法
            print(angle_start, angle_end)
            # from matlab import zeros, linspace
            t = linspace(angle_start, angle_end, steps)
            x_list = xc + abs(r) * cos(t) # t = list
            y_list = yc + abs(r) * sin(t)
            plt.plot(x_list, y_list)
            plt.show()
            xy = list(zip(x_list, y_list))
            print(xy)

        elif Rline.getElementsByTagName('spiral'): # 螺旋线
            from sympy import Symbol, integrate, sqrt, cos, pi, sin

            spiral = Rline.getElementsByTagName('spiral')[0]
            curvStart = float(spiral.getAttribute("curvStart"))
            curvEnd = float(spiral.getAttribute("curvEnd"))

            # TODO 曲率不是角度，要积分角度，角度可根据弧长和曲率算出
            len_init = length * (curvStart / (curvEnd - curvStart))  # 转化成初始曲率为0，从原点开始计算
            hdg_start = float(len_init * curvStart / 2)  # 算角度
            hdg_end = float(length * curvEnd / 2)

            ls = linspace(hdg_start, hdg_end, steps)
            len_ls = len(ls)

            # from matlab import integral
            t = Symbol("t")
            c1 = (1 / sqrt(2 * pi)) * (cos(t) / sqrt(t))
            s1 = (1 / sqrt(2 * pi)) * (sin(t) / sqrt(t))
            xy = zeros((len_ls, 2))
            ccc = sqrt(pi * length / abs(curvEnd))  # 半径R = 1/曲率

            # 计算初始曲率为0，起点为原点时的欧拉螺线 与 现有螺线的对应关系
            x_start = ccc * integrate(c1, (t, 0, ls[0]))
            y_start = ccc * integrate(s1, (t, 0, ls[0]))
            x_move = x - x_start
            y_move = y - y_start
            hdg_rotation = hdg - hdg_start
            def Coordinate_move_rotation(X, Y):
                # 1. 平移至初始位置 2.围绕初始点进行旋转
                X = X + x_move
                Y = Y + y_move
                # 旋转(hdg_rotation >0, 逆时针旋转， hdg_rotation <0, 顺时针旋转),旋转中心为起点xy
                nrx = (X - x) * cos(hdg_rotation) - (Y - y) * sin(hdg_rotation) + x
                nry = (X - x) * sin(hdg_rotation) + (Y - y) * cos(hdg_rotation) + y
                return nrx, nry

            for i in range(0, len_ls):
                C_ls = integrate(c1, (t, 0, ls[i]))
                S_ls = integrate(s1, (t, 0, ls[i]))
                X = ccc * C_ls
                Y = ccc * S_ls

                X, Y = Coordinate_move_rotation(X, Y)
                xy[i][0] = X
                xy[i][1] = Y

            plt.plot([i[0] for i in xy], [i[1] for i in xy], color="r", linestyle="", marker=".")
            plt.show()
            print(xy)

        elif Rline.getElementsByTagName('poly3'): #TODO 已放弃
            xy = []
            print(xy)
        elif Rline.getElementsByTagName('paramPoly3'):
            paramPoly3 = Rline.getElementsByTagName('paramPoly3')[0]  # 一个geometry只有一条参考线
            aU = float(paramPoly3.getAttribute('aU'))
            bU = float(paramPoly3.getAttribute('bU'))
            cU = float(paramPoly3.getAttribute('cU'))
            dU = float(paramPoly3.getAttribute('dU'))
            aV = float(paramPoly3.getAttribute('aV'))
            bV = float(paramPoly3.getAttribute('bV'))
            cV = float(paramPoly3.getAttribute('cV'))
            dV = float(paramPoly3.getAttribute('dV'))
            pRange = paramPoly3.getAttribute('dV')

            if pRange == "arcLength":
                p = length
            elif pRange == "normalized":
                p = 1
            else:
                p = float(pRange)

            xy = zeros((steps, 2))
            index = 0
            for i in linspace(0, p, steps):  # TODO PRANGE
                u = aU + bU * i + cU * i ** 2 + dU * i ** 3
                v = aV + bV * i + cV * i ** 2 + dV * i ** 3

                X, Y = Coordinate_rotation(u, v, hdg) # 转向，偏移
                X = x + X  # %x值平移；
                Y = Y + y  # %y值平移，后面不再重复；
                xy[index][0] = X
                xy[index][1] = Y
                index += 1
            plt.plot([i[0] for i in xy], [i[1] for i in xy], color="r", linestyle="", marker=".")
            plt.show()
            print(xy)
        else:
            raise Exception("Unknown Geometry !!!")
        init_xy.append(xy)

    return road_length, init_xy