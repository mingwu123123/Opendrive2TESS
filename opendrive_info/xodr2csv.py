import os
import json

import matplotlib.pyplot as plt
from lxml import etree
from commonroad.scenario.scenario import Scenario
from collections import defaultdict

from opendrive2lanelet.opendriveparser.elements.opendrive import OpenDrive
from opendrive2lanelet.network import Network
import csv

from opendrive2lanelet.opendriveparser.parser import parse_opendrive

from analy.utils import color_c
from opendrive_info.utils import convert_opendrive, get_lanes_info, write_lanes



if __name__ == "__main__":
    work_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genjson', 'genjson_files')
    file_name = "wanji_0701"
    filter_types = laneTypes = ["none", "driving", "stop", "shoulder", "biking", "sidewalk", "border", "restricted",
                                "parking", "median", "entry", "exit", "offRamp", "onRamp" 'curb', 'connectingRamp',]
    main(work_dir, file_name, filter_types=filter_types)
