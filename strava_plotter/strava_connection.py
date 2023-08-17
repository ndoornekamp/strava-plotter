import os
import requests
import webbrowser
import logging

from dotenv import load_dotenv
from urllib.error import HTTPError

load_dotenv('.env')

logger = logging.getLogger(__name__)


def authorise_app():
    """
    This function is used to obtain the authorisation code for making requests to Strava outside the context of a webserver
    It requires CLIENT_ID to be set as an environment variable

    To obtain the AUTH_CODE:
    - Go to this URL in a browser: https://www.strava.com/oauth/authorize?client_id=<CLIENT_ID>&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read
    - Authorise the app in the browser
    - From the URL you are redirected to, copy the 'code' part. This is your authentication code.
    """

    CLIENT_ID = os.getenv("CLIENT_ID")

    authorization_page_url = f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read"
    webbrowser.open(authorization_page_url)

    print("Authorise the app in your browser and copy the 'code' parameter from the URL you are redirected to, then press Enter")
    authorisation_code = input("code:")

    return authorisation_code


def get_strava_access_token(AUTHORISATION_CODE=None):
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")

    assert CLIENT_ID is not None
    assert CLIENT_SECRET is not None

    if not AUTHORISATION_CODE:
        AUTHORISATION_CODE = authorise_app()

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": AUTHORISATION_CODE,
        "grant_type": "authorization_code"
    }

    response = requests.post("https://www.strava.com/oauth/token", data=data)

    if response.status_code == 200:
        logger.info(f"Successfully obtained the access token for {response.json()['athlete']['firstname']} {response.json()['athlete']['lastname']}")
        return response.json()['access_token'], response.json()['athlete']['id']
    else:
        logger.info(f"Error obtaining access token: {response.json()}")
        raise HTTPError("https://www.strava.com/oauth/token", response.status_code, response.json(), None, None)


def get_rides_from_strava(TOKEN=None, authorisation_code=None, ATHLETE_ID=None):

    if not TOKEN:
        TOKEN, ATHLETE_ID = get_strava_access_token(AUTHORISATION_CODE=authorisation_code)

    headers = {"Authorization": f"Bearer {TOKEN}"}

    page = 1
    all_rides = []
    for page in range(1, 100):  # Loop through all pages (> 10000 activities seems unlikely..)
        logger.debug(f'Saving page {page} for athlete {ATHLETE_ID}')
        url = f"https://www.strava.com/api/v3/athlete/activities?per_page=100&page={page}"

        logger.debug(f"Sending request to {url}...")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Error : {response.text}")
            raise HTTPError(url=url, code=response.status_code, msg=f"Error: {response.text}", hdrs=headers, fp=None)

        rides_on_page = response.json()

        if not rides_on_page:  # Break once we've requested all rides (i.e. we receive empty pages back)
            all_rides = [ride for ride in all_rides if type(ride) is not str]
            logger.debug(f"Obtained {len(all_rides)} rides for athlete {ATHLETE_ID}")
            return all_rides

        all_rides += rides_on_page
