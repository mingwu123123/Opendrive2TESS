from pyproj import Proj
import csv

reader = csv.reader(open('轨迹_车辆轨迹.csv', 'r'))
writer = csv.writer(open('轨迹_车辆轨迹_2.csv', 'w', newline=''))

data = list()
header = next(reader)
data.append(header + ["经度", "纬度"])


# 点位偏移
x_move, y_move = (435.1175237488712 - (92.18007) + (-660.94688), 3758.567728138013 - (-458.675) + (-155.35))

p = Proj('+proj=tmerc +lon_0=119.91001546382904 +lat_0=30.510201559984594 +ellps=WGS84') # use kwargs
# print(p(0, 0, inverse=True))
for lane in reader:
    x, y = float(lane[6]), float(lane[7])
    x, y = x + x_move, y + y_move
    lon, lat = p(x, y, inverse=True)
    data.append(lane + [lon, lat])
    # print(lon, lat)

writer.writerows(data)
