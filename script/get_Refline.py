
def get_Refline(geometry):
    Rclinex = []
    Rcliney = []
    Rdirect = []
    Radd_length = []
    for Rline in geometry:
        step_length = 0.1  # TODO: # 以0.1m作为步长
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
        if Rline.getElementsByTagName('line'):
            while temp_Rlength + step_length < Rlength:
                temp_Rclinex.append(temp_Rclinex[-1] + step_length * math.cos(Rheading))
                temp_Rcliney.append(temp_Rcliney[-1] + step_length * math.sin(Rheading))
                temp_Rlength += step_length
                Rdirect.append(Rheading)
                Radd_length.append(Radd_length[-1] + step_length)
        elif Rline.getElementsByTagName('arc'):
            close2nextp = 0
            arc = Rline.getElementsByTagName('arc')
            curvature = float(arc[0].getAttribute('curvature'))
            delta_alpha = step_length * curvature
            temp_heading = Rheading
            while temp_Rlength + step_length < Rlength:
                #######
                # 用于平滑弧线/螺旋线尾端的累积误差，用直线连接目标点
                if Rline_index < len(geometry) - 1:
                    dist2nextp = math.sqrt((temp_Rclinex[-1] - nextx) ** 2 + (temp_Rcliney[-1] - nexty) ** 2)
                    # if dist2nextp < 0.2:
                    #     break
                    if dist2nextp < 1.0:
                        temp_heading = np.arctan2(nexty - temp_Rcliney[-1], nextx - temp_Rclinex[-1])
                        # if temp_heading < 0:
                        #     temp_heading += math.pi * 2
                        delta_alpha = 0
                        if close2nextp == 0:
                            Rlength = temp_Rlength + dist2nextp
                            close2nextp = 1
                #######
                temp_Rclinex.append(temp_Rclinex[-1] + step_length * math.cos(temp_heading))
                temp_Rcliney.append(temp_Rcliney[-1] + step_length * math.sin(temp_heading))
                temp_Rlength += step_length
                Rdirect.append(temp_heading)
                Radd_length.append(Radd_length[-1] + step_length)
                temp_heading += delta_alpha
        elif Rline.getElementsByTagName('spiral'):  # TODO:连接处做了平滑处理:是由于车道宽度导致的不平滑
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



