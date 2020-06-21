## A script for plotting Strava data
See https://nickdoornekamp.pythonanywhere.com/.

### Getting started
Note: the guide below was written for and tested on Linux. For running this on Windows, you'll need to download the the basemap-1.2.1-cp36-cp36m-win_amd64.whl file from https://www.lfd.uci.edu/~gohlke/pythonlibs/. (If you're running a 32-bit operating system, take basemap‑1.2.1‑cp36‑cp36m‑win32.whl instead, and update environment.yml for that)
1. Run "conda env create --name strava-plotter-env -f environment.yml"
2. Follow section B of [Strava's instructions for creating an app](https://developers.strava.com/docs/getting-started/). 
3. Rename '.env.example' to '.env' and fill the CLIENT_ID, CLIENT_SECRET you obtained in the previous steps.

### Running the the script
1. If desired, change the settings in settings.py
2. Run strava_plotter.py from the strava-plotter-env
3. Follow the instructions shown in the console
