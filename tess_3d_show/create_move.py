# import ifcopenshell
# ifc_file = ifcopenshell.open('test.ifc')
# products = ifc_file.by_type('IfcProduct')
# for product in products:
#     print(product.is_a())
from functools import reduce


# 創建墻
import Autodesk
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter, BuiltInCategory, Line, Wall, XYZ, Transaction

doc = __revit__.ActiveUIDocument.Document

levels = FilteredElementCollector(doc).OfCategory(
    BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
walls = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsElementType().ToElements()

for level in levels:
    elevation = level.get_Parameter(BuiltInParameter.LEVEL_ELEV).AsDouble()
    # if elevation == 3000 / 304.8:
    level_0 = level
for wall in walls:
    name = wall.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
    if name == '常规 - 200mm':
        wall_type = wall

p_1 = XYZ(0, 0, level_0.Elevation)
p_2 = XYZ(50, 0, level_0.Elevation)
p_3 = XYZ(50, 50, level_0.Elevation)
line_1 = Line.CreateBound(p_1, p_2)
line_2 = Line.CreateBound(p_2, p_3)
lines = [line_1, line_2]

t = Transaction(doc, '创建墙')
t.Start()
for line in lines:
    wall_1 = Wall.Create(doc, line, wall_type.Id, level_0.Id, 3000 / 304.8, 0, False, True)
    print(wall_1.Id)
t.Commit()

# 移动墙
import Autodesk
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInParameter, BuiltInCategory, Line, Wall, XYZ, Transaction
clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Transactions import TransactionManager

doc = __revit__.ActiveUIDocument.Document

levels = FilteredElementCollector(doc).OfCategory(
    BuiltInCategory.OST_Levels).WhereElementIsNotElementType().ToElements()
walls = FilteredElementCollector(doc).OfClass(Wall).ToElements()

t = Transaction(doc, '移动墙')
t.Start()
for element in walls:
    if element.Id.IntegerValue in [527874, 527876]:
        print("开始移动：{}".format(element.Id))
        print(element.Location.Curve.GetEndPoint(0))
    else:
        continue
    newLocation=XYZ(1,1,1)
    ElementTransformUtils.MoveElement(doc,element.Id,newLocation)
    element.Location.Curve.GetEndPoint(0)
    print(element.Location.Curve.GetEndPoint(0))
    print("移动成功")
    #输出
t.Commit()