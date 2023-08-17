def rectangles_overlap(rect_1, rect_2):
    """
    Returns True if rect_1 overlaps with rect_2, False otherwise
    """

    return not (rect_1['x_max'] < rect_2['x_min'] or  # rect_1 is completely on the left of rect_2
                rect_1['x_min'] > rect_2['x_max'] or  # rect_1 is completely on the right of rect_2
                rect_1['y_max'] < rect_2['y_min'] or  # rect_1 is completely below rect_2
                rect_1['y_min'] > rect_2['y_max'])    # rect_1 is completely above rect_2


def group_common_elements(input_list):
    """
    Groups lists with common elements (resulting in lists of bounding boxes that should be merged in this context)
    In: [[], [2], [1], [4], [3, 5], [4, 6], [5]]
    Out: [[0], [1, 2], [3, 4, 5, 6]]

    As discussed here: https://stackoverflow.com/questions/4842613/merge-lists-that-share-common-elements
    """

    input_list = [_list + [index] for index, _list in enumerate(input_list)]

    out = []
    while len(input_list)>0:
        first, *rest = input_list
        first = set(first)

        lf = -1
        while len(first)>lf:
            lf = len(first)

            rest2 = []
            for r in rest:
                if len(first.intersection(set(r)))>0:
                    first |= set(r)
                else:
                    rest2.append(r)
            rest = rest2

        out.append(first)
        input_list = rest

    output_list = [list(group) for group in out]

    return output_list


def group_overlapping(rides):
    """
    Groups any overlapping rides so that all rides that overlap are
    together in one list
    """

    bounding_boxes = [{
        "x_min": ride["min_lon"],
        "x_max": ride["max_lon"],
        "y_min": ride["min_lat"],
        "y_max": ride["max_lat"]
    } for ride in rides]

    bounding_box_overlaps = []
    for i, bounding_box_1 in enumerate(bounding_boxes):
        i_overlaps_with = []
        for j, bounding_box_2 in enumerate(bounding_boxes):
            if i != j and rectangles_overlap(bounding_box_1, bounding_box_2):
                i_overlaps_with.append(j)

        # bounding_box_overlaps is a list of lists, where the list at index i is a list of the indices of the bounding boxes that bounding box i overlaps with
        bounding_box_overlaps.append(i_overlaps_with)

    groups_of_overlapping_rides = group_common_elements(bounding_box_overlaps)

    ride_groups = [[rides[i] for i in group_of_overlapping_rides] for group_of_overlapping_rides in groups_of_overlapping_rides]

    return ride_groups