from math import sin

from matlab import zeros, linspace
import matplotlib.pyplot as plt

# 螺旋线
curvStart="-0.5" ;curvEnd="-1";
s="100.0";x="38.00"; y="-1.81" ;hdg="0.33" ;length="10";

# TODO 曲率不是角度，要积分角度，假设角度是0, 0.195
x = float(x)
y = float(y)
hdg = float(hdg)
length = float(length)
curvStart = float(curvStart)
curvEnd = float(curvEnd)
len_init = length * (curvStart/(curvEnd-curvStart)) # 转化成初始曲率为0的，从原点开始计算


# ls=0:0.001:0.1950;
# len_ls=length(ls);
hdg_start = len_init * curvStart / 2 #算角度
hdg_end = length * curvEnd / 2

ls = linspace(hdg_start, hdg_end, 10) # 这里应该是角度
len_ls = len(ls)

from sympy import Symbol, integrate, sqrt, cos, pi, sin
# from matlab import integral
t = Symbol("t")
c1=(1/sqrt(2*pi))*(cos(t)/sqrt(t))
s1=(1/sqrt(2*pi))*(sin(t)/sqrt(t))
xy=zeros((len_ls,2))
ccc=sqrt(pi*length/abs(curvEnd)) # 半径R = 1/曲率


# 完整展示
# ls = linspace(0, hdg_end, 10) #角度切分
# x_list = []
# y_list = []
# for i in range(len(ls)):
#     C_ls = integrate(c1, (t, 0, ls[i]))
#     S_ls = integrate(s1, (t, 0, ls[i]))
#     if ls[i] > hdg_start:
#         plt.plot([float(ccc*C_ls)], [float(ccc*S_ls)], color="r", linestyle="", marker=".")
#     else:
#         plt.plot([float(ccc * C_ls)], [float(ccc * S_ls)], color="b", linestyle="", marker=".")
# plt.show()

# x_start =float(ccc * integrate(c1, (t, 0, ls[0])))
# y_start =float(ccc * integrate(s1, (t, 0, ls[0])))
# x_move = x - x_start
# y_move = y - y_start
# hdg_rotation = hdg - hdg_start
#
# def Coordinate_move_rotation(X, Y):
#     # 1. 平移至初始位置 2.围绕初始点进行旋转
#     X = X + x_move
#     Y = Y + y_move
#     # 旋转(hdg_rotation >0, 逆时针旋转， hdg_rotation <0, 顺时针旋转),旋转中心为起点xy
#     nrx = (X - x) * cos(hdg_rotation) - (Y - y) * sin(hdg_rotation) + x
#     nry = (X - x) * sin(hdg_rotation) + (Y - y) * cos(hdg_rotation) + y
#     return nrx, nry
#
# for i in range(0, len_ls):
#     print(ls[0], ls[i])
#     # 第一个点总是 0,0 得出坐标后再旋转平移
#
#     C_ls=integrate(c1, (t, 0, ls[i]))
#     S_ls=integrate(s1, (t, 0, ls[i]))
#     X=float(ccc*C_ls) #ccc=o
#     Y=float(ccc*S_ls)
#
#     X, Y = Coordinate_move_rotation(X, Y)
#     xy[i][0]=X
#     xy[i][1]=Y
#     print(float(ccc*C_ls), float(ccc*S_ls))
#
# plt.plot([i[0] for i in xy], [i[1] for i in xy], color="r", linestyle="", marker=".")
# plt.show()

# l = ccc * sqrt(2*hdg_end / pi)


# 弧线
# x_arc=278 ;y_arc=-828;hdg_arc=0; s_arc=0 ;length_arc=500
# curvature=0.003
# r_arc=1/curvature
# xc=x_arc-r_arc*sin(hdg_arc)
# yc=y_arc+r_arc*cos(hdg_arc)
# print(xc, yc)
# theta=length_arc/r_arc  # 转动角度
# angle_start=pi/2-hdg_arc
# angle_end=theta+pi/2-hdg_arc
# print(angle_start, angle_end)
# t = linspace(-angle_start, angle_end, 10)
# print(t)
# x=xc+r_arc * cos(t)
# y= yc+r_arc*sin(t)
# plt.plot(x,y)
# plt.show()
# x_arc=0 ;y_arc=0;hdg_arc=0; s_arc=0 ;length_arc=1000
# curvature=0.003




x_arc=0 ;y_arc=0;hdg_arc=0; s_arc=0 ;length_arc=500
curvature=-0.003
r_arc=1/curvature #暂时不取绝对值
xc=x_arc-r_arc*sin(hdg_arc) # 圆心坐标（这种求法是否正确，可参照下方求点位的方法）
yc=y_arc+r_arc*cos(hdg_arc)
print(xc, yc)  #圆心
theta=length_arc/r_arc  # 转动角度

if curvature > 0: # 逆时针旋转
    if -pi <= hdg_arc < -pi/2: # 第三象限(-1/-0.5, 0.5/1)
        angle_start = hdg_arc + 1.5*pi
    elif -pi/2 <= hdg_arc < 0:# 第四象限(-0.5/0, -1/-0.5)
        angle_start = hdg_arc - 0.5*pi
    elif 0 <= hdg_arc < pi/2: # 第一象限(0/0.5, -0.5/0)
        angle_start = hdg_arc - 0.5*pi
    else: # 第二象限(0.5/1, 0/0.5)
        angle_start = hdg_arc - 0.5*pi
else: # 顺时针旋转
    if -pi <= hdg_arc < -pi/2: # 第三象限(-1/-0.5, -0.5/0)
        angle_start = hdg_arc + 0.5*pi
    elif -pi/2 <= hdg_arc < 0:# 第四象限(-0.5/0, 0/0.5)
        angle_start = hdg_arc + 0.5*pi
    elif 0 <= hdg_arc < pi/2: # 第一象限(0/0.5, 0.5/1)
        angle_start = hdg_arc + 0.5*pi
    else: # 第二象限(0.5/1, -1/-0.5)
        angle_start = hdg_arc - 1.5*pi

angle_end = angle_start + theta# 需要考虑转多圈，累加法
print(angle_start, angle_end)
t = linspace(float(angle_start), float(angle_end), 100)
x = xc+ abs(r_arc) * cos(t)
y = yc + abs(r_arc) * sin(t)

# angle_start=pi/2-hdg_arc
# angle_end=theta+pi/2-hdg_arc
# print(angle_start, angle_end)
# t = linspace(angle_start, angle_end, 100)
# x=xc+r_arc * sin(t + hdg_arc)
# y= yc - r_arc*cos(t + hdg_arc)
plt.plot(x,y)
plt.show()



import os
os._exit(1)


# 参数三项式
# 若@pRange="arcLength"，那么p可（may）在[0, @length from <geometry> ]范围内对其赋值。
# 若@pRange="normalized"，那么p可（may）在[0, 1]范围内对其赋值。
def Coordinate_rotation(X,Y,theta): #%X、Y是局部坐标值，theta对应于hdg角度,x、y全局坐标值。
    x=X*cos(theta)-Y*sin(theta);
    y=X*sin(theta)+Y*cos(theta);
    return x, y

s="0"
x="6.8"
y="5.4"
hdg="5.2"
length="10"
aU="0"
bU="1.0"
cU="-4.66e-09"
dU="-2.62e-08"
aV="0.00e+00"
bV="1.66e-16"
cV="-1.98e-04"
dV="-1.31e-09"
pRange="arcLength"
s=double(s);
x=double(x);

y=double(y);
hdg=double(hdg);

length=double(length);

aU=double(aU);
bU=double(bU);
cU=double(cU);
dU=double(dU);
aV=double(aV);
bV=double(bV);
cV=double(cV);
dV=double(dV);

uv=zeros((100,2));
index=0;
for i in linspace(0,10,100): #TODO PRANGE
    u=aU+bU*i+cU*i**2+dU*i**3;
    v=aV+bV*i+cV*i**2+dV*i**3;
    from matlab import rot90
    [ X,Y]=Coordinate_rotation(u,v,hdg)
    X=x+X; #%x值平移；
    Y=Y+y; #%y值平移，后面不再重复；
    uv[index][0]=X;
    uv[index][1]=Y;
    index += 1
print(uv)
plt.plot([i[0] for i in uv], [i[1] for i in uv], color="r", linestyle="", marker=".")
plt.show()
import os
os._exit(1)

s1="0.000000000000e+00"; x1="-2.855056647744e+03" ;y1="5.163670291832e+03"; hdg1="3.678546924447e-02"; length1="2.500078567784e+01";
aU1="0.000000000000e+00"; bU1="2.500000000001e+01" ;cU1="-1.179775702581e-02" ;dU1="5.898878510380e-03"; aV1="0.000000000000e+00"; bV1="0.000000000000e+00" ;cV1="1.086110728936e+00"; dV1="-5.430553643517e-01" ;pRange1=1;

s2="2.500078567784e+01"; x2="-2.830099427400e+03"; y2="5.165132192211e+03" ;hdg2="5.850939248778e-02" ;length2="2.500000000004e+01";
aU2="0.000000000000e+00"; bU2="2.500000000004e+01" ;cU2="-2.433465986771e-14"; dU2="1.625209696867e-14" ;aV2="0.000000000000e+00" ;bV2="2.220446049250e-16"; cV2="6.938933641603e-10" ;dV2="-4.614609867787e-10"; pRange2=1;

s3="5.000078567788e+01" ;x3="-2.805142207057e+03" ;y3="5.166594092591e+03" ;hdg3="5.850939248792e-02"; length3="2.499999999990e+01";
aU3="0.000000000000e+00"; bU3="2.499999999990e+01" ;cU3="1.028584409687e-15"; dU3="0.000000000000e+00" ;aV3="0.000000000000e+00"; bV3="0.000000000000e+00"; cV3="-5.225974468605e-10" ;dV3="2.935688096311e-10" ;pRange3=1;

s4="7.500078567777e+01"; x4="-2.780184986713e+03"; y4="5.168055992971e+03"; hdg4="5.850939248134e-02"; length4="3.259185499839e+01";
aU4="0.000000000000e+00" ;bU4="3.259077023178e+01" ;cU4="8.141001992985e-03"; dU4="-8.141001992975e-03"; aV4="0.000000000000e+00" ;bV4="2.220446049250e-16"; cV4="-7.284070115927e-01" ;dV4="7.284070116768e-01" ;pRange4=1;

s1=double(s1);
s2=double(s2);
s3=double(s3);
s4=double(s4);

x1=double(x1);
x2=double(x2);
x3=double(x3);
x4=double(x4);
y1=double(y1);
y2=double(y2);
y3=double(y3);
y4=double(y4);
hdg1=double(hdg1);
hdg2=double(hdg2);
hdg3=double(hdg3);
hdg4=double(hdg4);
length1=double(length1);
length2=double(length2);
length3=double(length3);
length4=double(length4);

aU1=double(aU1);
aU2=double(aU2);
aU3=double(aU3);
aU4=double(aU4);
bU1=double(bU1);
bU2=double(bU2);
bU3=double(bU3);
bU4=double(bU4);
cU1=double(cU1);
cU2=double(cU2);
cU3=double(cU3);
cU4=double(cU4);
dU1=double(dU1);
dU2=double(dU2);
dU3=double(dU3);
dU4=double(dU4);

aV1=double(aV1);
aV2=double(aV2);
aV3=double(aV3);
aV4=double(aV4);
bV1=double(bV1);
bV2=double(bV2);
bV3=double(bV3);
bV4=double(bV4);
cV1=double(cV1);
cV2=double(cV2);
cV3=double(cV3);
cV4=double(cV4);
dV1=double(dV1);
dV2=double(dV2);
dV3=double(dV3);
dV4=double(dV4);


uv1=zeros((100,2));
index1=0;
for i1 in linspace(0,1,100): # prange(1) i1 是公共参数，需要自己去算的插值，而这个p的取值范围就是（0，pRange）
                             # 假设length = 1000，分段长5，切分200段，p1=prange/200 = prange/(length/dis)
    u1=aU1+bU1*i1+cU1*i1**2+dU1*i1**3;
    v1=aV1+bV1*i1+cV1*i1**2+dV1*i1**3;
    from matlab import rot90
    [ X1,Y1]=Coordinate_rotation(u1,v1,hdg1)
    X1=x1+X1; #%x值平移；
    Y1=Y1+y1; #%y值平移，后面不再重复；
    uv1[index1][0]=X1;
    uv1[index1][1]=Y1;
    index1 += 1;

plt.plot([i[0] for i in uv1], [i[1] for i in uv1], color="r", linestyle="", marker=".")


uv2=zeros((100,2));
index2=0;
for i2 in linspace(0,1,100):
    u2=aU2+bU2*i2+cU2*i2**2+dU2*i2**3;
    v2=aV2+bV2*i2+cV2*i2**2+dV2*i2**3;
    [ X2,Y2]=Coordinate_rotation(u2,v2,hdg2);
    X2=x2+X2;
    Y2=Y2+y2;
    uv2[index2][0]=X2;
    uv2[index2][1]=Y2;
    index2+=1;
plt.plot([i[0] for i in uv2], [i[1] for i in uv2], color="y", linestyle="", marker=".")

uv3=zeros((100,2));
index3=0;
for i3 in linspace(0,1,100):
    u3=aU3+bU3*i3+cU3*i3**2+dU3*i3**3;
    v3=aV3+bV3*i3+cV3*i3**2+dV3*i3**3;
    [ X3,Y3]=Coordinate_rotation(u3,v3,hdg3);
    X3=x3+X3;
    Y3=Y3+y3;
    uv3[index3][0]=X3;
    uv3[index3][1]=Y3;
    index3+=1;
plt.plot([i[0] for i in uv3], [i[1] for i in uv3], color="b", linestyle="", marker=".")


uv4=zeros((100,2));
index4=0;
for i4 in linspace(0,1,100):
    u4=aU4+bU4*i4+cU4*i4**2+dU4*i4**3;
    v4=aV4+bV4*i4+cV4*i4**2+dV4*i4**3;

    [ X4,Y4]=Coordinate_rotation(u4,v4,hdg4);
    X4=x4+X4;
    Y4=Y4+y4;
    uv4[index4][0]=X4;
    uv4[index4][1]=Y4;
    index4+=1;
plt.plot([i[0] for i in uv4], [i[1] for i in uv4], color="r", linestyle="", marker=".")
plt.show()
# point=zeros(404,2);
# for j=1:101
#     point(j,1)=uv1(j,1);
#     point(j,2)=uv1(j,2);
#     point(j+101,1)=uv2(j,1);
#     point(j+101,2)=uv2(j,2);
#     point(j+101*2,1)=uv3(j,1);
#     point(j+101*2,2)=uv3(j,2);
#     point(j+101*3,1)=uv4(j,1);
#     point(j+101*3,2)=uv4(j,2);
# end
# figure(5)
# plot(point(:,1),point(:,2))

