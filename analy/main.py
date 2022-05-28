import os

import xodr2csv
import roads_relation

if __name__ == '__main__':
    step_length = 0.5
    show = True
    # 定义静态文件及所处位置文件夹
    work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
    file_name = 'test3'

    # TODO 注意对第三方包的修改 --> change_convert.py
    lanes_info = xodr2csv.main(work_dir, file_name, step_length, show=show, filter_types=None)
    roads_info = roads_relation.main(work_dir, file_name, step_length=step_length, show=show)
    print(lanes_info)
    print(roads_info)
