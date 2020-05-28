import json
import os
import polyline
import base64

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from mpl_toolkits.basemap import Basemap
from math import floor
from io import BytesIO

from constants import RESULTS_FOLDER
from settings import MARGIN, IDS_TO_SKIP, CLUSTERED, FIRST_CLUSTER_ONLY, SUBPLOTS_IN_SEPARATE_FILES, OUTPUT_FORMAT
from strava_connection import get_rides_from_strava
from group_overlapping import group_overlapping


def get_bounding_box(coordinates):
    """
    Given a list of coordinates, returns a bounding box that contains all these coordinates
    """

    longitudes = [coordinate[1] for coordinate in coordinates]
    latitudes = [coordinate[0] for coordinate in coordinates]

    bounding_box = {}

    bounding_box["min_lon"] = min(longitudes) - MARGIN
    bounding_box["width"] = max(longitudes) - min(longitudes) + 2*MARGIN
    bounding_box["min_lat"] = min(latitudes) - MARGIN
    bounding_box["height"] = max(latitudes) - min(latitudes) + 2*MARGIN

    return bounding_box


def parse_rides(rides):
    """
    Parses the rides obtained from Strava to a list, containing a dictionary with a bounding box 
    and a list of coordinates per ride
    """

    rides_parsed = []

    for ride in rides:
        if str(ride['id']) in IDS_TO_SKIP:
            continue

        if ride['map']['summary_polyline']:  # Not all rides have a polyline
            coordinates = polyline.decode(ride['map']['summary_polyline'])
        else:
            continue

        bounding_box = get_bounding_box(coordinates)

        rides_parsed.append({
            "bottom": bounding_box["min_lat"],
            "left": bounding_box["min_lon"],
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


def get_ride_cluster_bounding_boxes(ride_groups):
    
    ride_group_bounding_boxes =[]
    for ride_group in ride_groups:
        ride_group_coordinates = []

        for ride in ride_group:
            ride_group_coordinates += [coordinate for coordinate in ride["coordinates"]]
        
        ride_group_bounding_box = get_bounding_box(ride_group_coordinates)
        ride_group_bounding_boxes.append(ride_group_bounding_box)
    
    return ride_group_bounding_boxes


def plot_rides(ride_clusters):
    
    ride_cluster_bounding_boxes = get_ride_cluster_bounding_boxes(ride_clusters)
    widths = [bounding_box['width'] for bounding_box in ride_cluster_bounding_boxes]
    heights = [bounding_box['height'] for bounding_box in ride_cluster_bounding_boxes]
    
    nof_rows = 1
    nof_columns = len(ride_clusters)
    gs = gridspec.GridSpec(nof_rows, nof_columns, width_ratios=widths)
    images_base64 = []

    for i, ride_cluster in enumerate(ride_clusters):
        ride_cluster_bounding_box = ride_cluster_bounding_boxes[i]

        if not SUBPLOTS_IN_SEPARATE_FILES:
            ax = plt.subplot(gs[i])
            map_ax = plot_cluster(ax, ride_cluster_bounding_box, ride_cluster)
        else:
            ax = plt.subplot(gridspec.GridSpec(1, 1, width_ratios=[widths[i]])[0])
            map_ax = plot_cluster(ax, ride_cluster_bounding_box, ride_cluster)

            if OUTPUT_FORMAT == 'bytes':
                images_base64.append(plot_to_bytes(plt, width=widths[i], height=heights[i]))
            else:
                output_path = os.path.join(RESULTS_FOLDER, f'output{i}.png')

                if not os.path.isdir(RESULTS_FOLDER):
                    os.mkdir(RESULTS_FOLDER)

                plt.savefig(output_path, dpi=600)        

    if SUBPLOTS_IN_SEPARATE_FILES:
        if OUTPUT_FORMAT == 'bytes':
            return images_base64
        else:
            raise NotImplementedError(f"Saving subplots in separate files with output format {OUTPUT_FORMAT} is not yet implemented")
    else:
        plt.subplots_adjust(left=0.03, bottom=0.05, right=0.97, top=0.95, wspace=0.1, hspace=0.1)
        if OUTPUT_FORMAT == 'bytes':
            return [plot_to_bytes(plt)]
        elif OUTPUT_FORMAT == "image":
            output_path = os.path.join(RESULTS_FOLDER, 'output.png')

            if not os.path.isdir(RESULTS_FOLDER):
                os.mkdir(RESULTS_FOLDER)

            plt.savefig(output_path, dpi=600)
        else:
            raise NotImplementedError(f"Unknown {OUTPUT_FORMAT}: expected either 'bytes' or 'image'")


def plot_cluster(ax, ride_cluster_bounding_box, ride_cluster):
    """
    Given a list of rides and its bounding box, plots this cluster the matplotlib object <ax>,
    with satellite imagery as background 
    """

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
        xpixels=min(2000, 600*ride_cluster_bounding_box['width'])
    )

    for ride in ride_cluster:
        ride_longitudes = [coordinate[1] for coordinate in ride["coordinates"]]
        ride_latitudes = [coordinate[0] for coordinate in ride["coordinates"]]

        x, y = map_ax(ride_longitudes, ride_latitudes)
        map_ax.plot(x, y, 'r-', alpha=0.5, linewidth=0.2)
    
    return map_ax


def plot_to_bytes(plt, width=None, height=None):

    if width and height:
        plt.gcf().set_size_inches(2*width, 2*height)

    plt.gca().set_axis_off()
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=600, bbox_inches = 'tight', pad_inches = 0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()

    return image_base64


def strava_plotter(authorisation_code):
    os.chdir(os.path.dirname(__file__))  # Set working directory to script directory
    rides_raw = get_rides_from_strava(authorisation_code=authorisation_code)
    rides = parse_rides(rides_raw)
    ride_clusters = cluster_rides(rides)
    plot_rides(ride_clusters)


if __name__ == "__main__":
    strava_plotter(authorisation_code=None)
