import os

import xodr2csv
import roads_relation

num = 3
step_length = 0.5
work_dir = os.getcwd()
lanes_info = xodr2csv.main(num, work_dir, step_length, show=False, filter_types=None)
roads_info = roads_relation.main(num, work_dir, step_length=0.5, show=False)
print(lanes_info)
print(roads_info)


