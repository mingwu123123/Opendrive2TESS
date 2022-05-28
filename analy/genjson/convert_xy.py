# import js2py
#
# with open('genjson_files/proj4-src.js') as f:
#     js_content = f.read()
#
# context = js2py.EvalJs()
# context.execute(js_content)
# # result = context.defs('WGS84', "+title=WGS 84 (long/lat) +proj=longlat +ellps=WGS84 +datum=WGS84 +units=degrees")
# result = context.defs(
#
# )
# print(result)

import pyproj

# pyproj.transform()

def proj_trans():

    # 读取经纬度
    #
    # data = pd.read_excel(u"D:/Visualization/python/file/location.xlsx")
    #
    # lon = data.lon.values
    #
    # lat = data.lat.values
    #
    # print lon, lat
    lon = [116.366]
    lat = [39.8673]

    p1 = pyproj.Proj(init="epsg:4326")  # 定义数据地理坐标系

    p2 = pyproj.Proj(init="epsg:3857")  # 定义转换投影坐标系

    x1, y1 = p1(lon, lat)

    x2, y2 = pyproj.transform(p1, p2, x1, y1, radians=True)
    print(x2, y2)
# proj_trans()

from pyproj import Proj


p = Proj(proj='tmerc', ellps='WGS84', preserve_units=False) # use kwargs
x,y = p(116.2872229585798, 40.04753227284374)
print(tuple((x,y)))
lons = (-119.72,-118.40,-122.38)
lats = (36.77, 33.93, 37.62 )
x,y = p(lons, lats)
print(x,y)

p = Proj('+proj=tmerc +lon_0=116.2872229585798 +lat_0=40.04753227284374 +ellps=WGS84') # use kwargs
x,y = p(0, 0, inverse=True)
print(x,y)