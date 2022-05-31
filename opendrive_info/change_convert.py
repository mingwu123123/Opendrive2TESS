def export_lanelet_network(
        self, filter_types: list = None
) -> "ConversionLaneletNetwork":
    """Export network as lanelet network.

    Args:
      filter_types: types of ParametricLane objects to be filtered. (Default value = None)

    Returns:
      The converted LaneletNetwork object.
    """

    # Convert groups to lanelets
    lanelet_network = ConversionLaneletNetwork()

    for parametric_lane in self._planes:
        if filter_types is not None and parametric_lane.type not in filter_types:
            continue
        init_id = parametric_lane.id_.split('.')[0]
        # 在这里添加 lanelet 的 原始信息
        # 所有路段都会有这个属性,调整精度
        lanelet = parametric_lane.to_lanelet(0.5) # 精度调整

        lanelet.lane_name = parametric_lane.id_
        lanelet.type = parametric_lane.type

        lanelet.predecessor = self._link_index.get_predecessors(parametric_lane.id_)
        lanelet.successor = self._link_index.get_successors(parametric_lane.id_)

        lanelet_network.add_lanelet(lanelet)

    # prune because some
    # successorIds get encoded with a non existing successorID
    # of the lane link

    # 此处进行了车道合并和修复,TESS并不需要
    # lanelet_network.prune_network()
    # lanelet_network.concatenate_possible_lanelets()

    # Perform lane splits and joins
    # lanelet_network.join_and_split_possible_lanes()

    # lanelet_network.convert_all_lanelet_ids()

    return lanelet_network

