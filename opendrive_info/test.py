#
# from numpy import sqrt, square
# width = 1
# def get_coo(coo1, coo2, right=T):
#     x1, y1, x2, y2 = coo1[0], coo1[1], coo2[0], coo2[1]
#     X = x1 + width * (y2 - y1) / sqrt(square(x2-x1) + square((y2-y1)))
#     Y = y1 + width * (x1 - x2) / sqrt(square(x2-x1) + square((y2-y1)))
#     print(X, Y)
#
# get_coo([0,0], [1, 1])
# get_coo([0,0], [1, 0])
# get_coo([0,0], [-1, -1])
# get_coo([0,0], [1, -1])
# get_coo([0,0], [-1, 1])


a = [1,2,3]
b = [4]
print(bool(set(a) & set(b)))