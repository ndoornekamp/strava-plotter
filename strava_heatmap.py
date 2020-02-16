"""
Connects to the Strava API to plot rides
"""

import json
import os
import polyline
import logging

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from mpl_toolkits.basemap import Basemap
from math import floor

from constants import RIDES_JSON_PATH, MARGIN, IDS_TO_SKIP, CLUSTERED, FIRST_CLUSTER_ONLY
from strava_connection import save_rides_to_json
from group_overlapping import group_overlapping

logger = logging.getLogger(__name__)


def get_bounding_box(coordinates):
    """
    Given a list of coordinates, provides a bounding box that contains all these coordinates
    """

    longitudes = [coordinate[1] for coordinate in coordinates]
    latitudes = [coordinate[0] for coordinate in coordinates]

    bounding_box = {}

    bounding_box["min_lon"] = min(longitudes) - MARGIN
    bounding_box["height"] = max(longitudes) - bounding_box["min_lon"] + MARGIN
    bounding_box["min_lat"] = min(latitudes) - MARGIN
    bounding_box["width"] = max(latitudes) - bounding_box["min_lat"] + MARGIN

    return bounding_box


def parse_rides():
    """
    Parses the all_rides.json to a list, containing a dictionary with a bounding box and a list of coordinates per ride
    """

    with open(RIDES_JSON_PATH, 'r') as infile:
        rides = json.load(infile)

    rides_parsed = []

    for ride in rides:
        if ride['upload_id_str'] in IDS_TO_SKIP:
            continue

        coordinates = polyline.decode(ride['map']['summary_polyline'])

        bounding_box = get_bounding_box(coordinates)

        rides_parsed.append({
            "bottom": bounding_box["min_lon"],
            "left": bounding_box["min_lat"],
            "width": bounding_box["width"],
            "height": bounding_box["height"],
            "coordinates": coordinates
        })

    return rides_parsed


def cluster_rides(rides):
    if CLUSTERED:
        ride_clusters = group_overlapping(rides)
        if FIRST_CLUSTER_ONLY:
            ride_clusters = [ride_clusters[0]]
    else:
        ride_clusters = [rides]
    
    return ride_clusters


def get_ride_cluster_bounding_boxes(route_groups):
    
    widths = []
    route_group_bounding_boxes =[]
    for route_group in route_groups:
        route_group_coordinates = []
        for route in route_group:
            route_group_coordinates += [coordinate for coordinate in route["coordinates"]]
        
        route_group_bounding_box = get_bounding_box(route_group_coordinates)
        route_group_bounding_boxes.append(route_group_bounding_box)
        widths.append(route_group_bounding_box["width"])
    
    return widths, route_group_bounding_boxes


def plot_rides(ride_clusters):
    nof_rows = 1
    nof_columns = len(ride_clusters)
    
    widths, ride_cluster_bounding_boxes = get_ride_cluster_bounding_boxes(ride_clusters)

    gs = gridspec.GridSpec(nof_rows, nof_columns, width_ratios=widths)

    for i, ride_cluster in enumerate(ride_clusters):
        ride_cluster_bounding_box = ride_cluster_bounding_boxes[i]

        ax = plt.subplot(gs[i])

        map_ax = Basemap(
            llcrnrlon=ride_cluster_bounding_box["min_lon"],  # Left
            llcrnrlat=ride_cluster_bounding_box["min_lat"],  # Down
            urcrnrlon=ride_cluster_bounding_box["min_lon"] + ride_cluster_bounding_box["width"],  # Right
            urcrnrlat=ride_cluster_bounding_box["min_lat"] + ride_cluster_bounding_box["height"],  # Up
            epsg=23095,
            ax = ax
        )

        map_ax.arcgisimage(
            service="World_Imagery",
            xpixels=min(600*widths[i], 2000)
        )

        for ride in ride_cluster:
            ride_longitudes = [coordinate[1] for coordinate in ride["coordinates"]]
            ride_latitudes = [coordinate[0] for coordinate in ride["coordinates"]]

            x, y = map_ax(ride_longitudes, ride_latitudes)
            map_ax.plot(x, y, 'r-', alpha=1)

    plt.subplots_adjust(left=0.03, bottom=0.05, right=0.97, top=0.95, wspace=0.1, hspace=0.1)
    plt.show()


if __name__ == "__main__":
    if not os.path.isfile(RIDES_JSON_PATH):
        save_rides_to_json()
       
    rides = parse_rides()
    ride_clusters = cluster_rides(rides)
    
    plot_rides(ride_clusters)