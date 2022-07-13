from pyproj import Proj
import csv

reader = csv.reader(open('轨迹_车辆轨迹.csv', 'r'))
next(reader)


x_move, y_move = (435.1175237488712 - (92.18007) + (-660.94688), 3758.567728138013 - (-458.675) + (-155.35))

p = Proj('+proj=tmerc +lon_0=119.91001546382904 +lat_0=30.510201559984594 +ellps=WGS84') # use kwargs
print(p(0, 0, inverse=True))
for lane in reader:
    x, y = lane[6], lane[7]
    x, y = x + x_move, y + y_move
    lon, lat = p(x, y, reversed=True)
    print(lon, lat)



xy_limit = [-776.558614300042, -733.9176933802678, 3308.807624498371, 3336.3131050797983]
x_move, y_move = sum(xy_limit[:2]) / 2, sum(xy_limit[2:]) / 2 if xy_limit else (0, 0)

# p = Proj('+proj=tmerc +lon_0=119.91001546382904 +lat_0=30.510201559984594 +ellps=WGS84')
# x, y = -25, -7
# x, y = x / 1.33 + x_move,-( y/1.33) + y_move
# print(p(x, y, inverse=True))


# 上：119.90401335060596,30.555825645199448
# 下：119.90892481058835,30.537969697359024
# 左：119.90360632538795,30.541203588335247
# 浙江高速门架经纬度：[119.90693092346191, 30.544096644107]
