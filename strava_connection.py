import os
import requests
import logging
import webbrowser
import json

from dotenv import load_dotenv

from constants import RIDES_JSON_PATH

load_dotenv()
logger = logging.getLogger(__name__)


def authorize_app():
    CLIENT_ID = os.getenv("CLIENT_ID")

    authorization_page_url = f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read"
    webbrowser.open(authorization_page_url)


def get_strava_access_token():
    """
    To obtain the AUTH_CODE:
    - Go to this URL in a browser: https://www.strava.com/oauth/authorize?client_id=<CLIENT_ID>&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read
    - Authorize the app
    - From the URL you are redirected to, copy the 'code' part 
    """
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    AUTH_CODE = os.getenv("AUTH_CODE")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": AUTH_CODE,
        "grant_type": "authorization_code"
    }

    response = requests.post("https://www.strava.com/oauth/token", data=data)

    if "access_token" not in response.json():
        logger.error("Authorization failed! Please authorize the app in your browser, copy the 'code' parameter from the URL you are redirected to, and paste it in your .env file. Then run this function again.")
        authorize_app()
    else:
        return response.json()['access_token']


def save_rides_to_json():
    """
    Get all activities from Strava, save them as a local JSON
    """

    TOKEN = get_strava_access_token()
    ATHLETHE_ID = os.getenv("ATHLETE_ID")

    url = f"https://www.strava.com/api/v3/athletes/{ATHLETHE_ID}/activities"
    headers = {"Authorization": f"Bearer {TOKEN}"}

    page = 1
    all_rides = []
    while True:  # Loop through all pages
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


def get_rides(TOKEN, ATHLETE_ID):
    url = f"https://www.strava.com/api/v3/athletes/{ATHLETHE_ID}/activities"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    data = {"per_page": 10, "page": 1}
    response = requests.get(url, headers=headers, data=data)
    return response.json()


if __name__ == "__main__":
    
    TOKEN = get_strava_access_token()
    ATHLETHE_ID = os.getenv("ATHLETE_ID")

    print(get_rides(TOKEN, ATHLETHE_ID))
    # save_rides_to_json()
