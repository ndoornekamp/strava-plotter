import os
import requests
import webbrowser
import json

from dotenv import load_dotenv
from urllib.error import HTTPError

load_dotenv('.env')


def authorise_app():
    """
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
        print(f"Successfully obtained the access token for {response.json()['athlete']['firstname']} {response.json()['athlete']['lastname']}")
        return response.json()['access_token'], response.json()['athlete']['id']
    else:
        print(f"Error obtaining access token: {response.json()}")
        raise HTTPError("https://www.strava.com/oauth/token", response.status_code, response.json(), None, None)


def get_rides_from_strava(TOKEN=None, authorisation_code=None, ATHLETE_ID=None):
    """
    Get all activities from Strava, save them as a local JSON
    """

    if not TOKEN:
        TOKEN, ATHLETE_ID = get_strava_access_token(AUTHORISATION_CODE=authorisation_code)

    url = f"https://www.strava.com/api/v3/athletes/{ATHLETE_ID}/activities"
    headers = {"Authorization": f"Bearer {TOKEN}"}

    page = 1
    all_rides = []
    for page in range(1, 100):  # Loop through all pages (> 10000 activities seems unlikely..)
        print(f'Saving page {page} for athlete {ATHLETE_ID}')
        data = {
            "per_page": 100,
            "page": page
        }

        response = requests.get(url, headers=headers, data=data)

        if response.status_code != 200:
            print(f"Error : {response.json()}")
            raise HTTPError(url=url, code=response.status_code, msg=f"Error: {response.json()}", hdrs=headers, fp=None)

        rides_on_page = response.json()

        if rides_on_page == []:  # Break once we've requested all rides (i.e. we receive empty pages back)
            break

        all_rides += response.json()

    all_rides = [ride for ride in all_rides if type(ride) is not str]

    print(f"Obtained {len(all_rides)} rides for athlete {ATHLETE_ID}")

    return all_rides
