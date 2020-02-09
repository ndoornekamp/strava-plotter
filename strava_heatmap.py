"""
Connects to the Strava API to plot rides
"""

import requests
import json
import os
import polyline
import logging

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from mpl_toolkits.basemap import Basemap
from math import floor
from dotenv import load_dotenv

from group_overlapping import group_overlapping

logger = logging.getLogger(__name__)
load_dotenv()

MARGIN = 0.2
RIDES_JSON_PATH = os.path.join('strava-heatmap', 'all_rides.json')
IDS_TO_SKIP = ['676955219']


def connect_to_strava_api():
    """
    To obtain 'code':
    - Go to this URL in a browser: https://www.strava.com/oauth/authorize?client_id=36057&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read
    - Authorize the app
    - From the URL you are redirected to, copy the 'code' part 
    """

    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    AUTH_CODE = os.getenv("AUTH_CODE")
    CLIENT_ID = os.getenv("CLIENT_ID")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": AUTH_CODE,
        "grant_type": "authorization_code"
    }

    response = requests.post("https://www.strava.com/oauth/token", data=data)

    logger.debug(response.json())

    return response.json()['access_token']


def get_rides():

    TOKEN = connect_to_strava_api()

    url = "https://www.strava.com/api/v3/athletes/8952599/activities"
    headers = {"Authorization": f"Bearer {TOKEN}"}

    page = 1
    all_rides = []

    while True:
        data = {
            "per_page": 100,
            "page": page
        }
        
        response = requests.get(url, headers=headers, data=data)
        logger.debug(response.json())
        rides_on_page = response.json()

        if rides_on_page == []:
            break

        all_rides += response.json()
        page += 1
    
    all_rides = [ride for ride in all_rides if type(ride) is not str and ride['type']=="Ride"]

    with open(RIDES_JSON_PATH, 'w') as outfile:
        json.dump(all_rides, outfile, indent=4)


def get_bounding_box(coordinates):
    """
    Given a list of coordinates, provides a bounding box that contains all these coordinates
    """

    longitudes = [coordinate[0] for coordinate in coordinates]
    latitudes = [coordinate[1] for coordinate in coordinates]

    bounding_box = {}

    bounding_box["min_lon"] = min(longitudes) - MARGIN
    bounding_box["height"] = max(longitudes) - bounding_box["min_lon"] + MARGIN
    bounding_box["min_lat"] = min(latitudes) - MARGIN
    bounding_box["width"] = max(latitudes) - bounding_box["min_lat"] + MARGIN

    return bounding_box


def parse_rides(rides):
    routes = []

    for ride in rides:
        if ride['upload_id_str'] in IDS_TO_SKIP:
            continue

        coordinates = polyline.decode(ride['map']['summary_polyline'])

        bounding_box = get_bounding_box(coordinates)

        routes.append({
            "bottom": bounding_box["min_lon"],
            "left": bounding_box["min_lat"],
            "width": bounding_box["width"],
            "height": bounding_box["height"],
            "coordinates": coordinates
        })

    return routes


def get_route_group_bounding_boxes(route_groups):
    
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


def plot_routes(route_groups):
    nof_rows = 1
    nof_columns = len(route_groups)
    
    widths, route_group_bounding_boxes = get_route_group_bounding_boxes(route_groups)

    gs = gridspec.GridSpec(nof_rows, nof_columns, width_ratios=widths)

    for i, route_group in enumerate(route_groups):
        route_group_bounding_box = route_group_bounding_boxes[i]

        ax = plt.subplot(gs[i])

        map_ax = Basemap(
            llcrnrlon=route_group_bounding_box["min_lat"],  # Left
            llcrnrlat=route_group_bounding_box["min_lon"],  # Down
            urcrnrlon=route_group_bounding_box["min_lat"] + route_group_bounding_box["width"],  # Right
            urcrnrlat=route_group_bounding_box["min_lon"] + route_group_bounding_box["height"],  # Up
            epsg=23095,
            ax = ax,
        )

        map_ax.arcgisimage(
            service="World_Imagery",
            xpixels=min(600*widths[i], 2000),
            verbose= True
        )

        for route in route_group:
            route_longitudes = [coordinate[0] for coordinate in route["coordinates"]]
            route_latitudes = [coordinate[1] for coordinate in route["coordinates"]]

            x, y = map_ax(route_latitudes, route_longitudes)
            map_ax.plot(x, y, 'r-', alpha=1)

    plt.subplots_adjust(left=0.03, bottom=0.05, right=0.97, top=0.95, wspace=0.1, hspace=0.1)
    plt.show()


if __name__ == "__main__":
    CLUSTERED = True
    FIRST_CLUSTER_ONLY = False

    if not os.path.isfile(RIDES_JSON_PATH):
        get_rides()
    
    with open(RIDES_JSON_PATH, 'r') as infile:
        rides = json.load(infile)
    
    routes = parse_rides(rides)

    if CLUSTERED:
        route_groups = group_overlapping(routes)
        if FIRST_CLUSTER_ONLY:
            route_groups = [route_groups[0]]
    else:
        route_groups = [routes]
    
    plot_routes(route_groups)