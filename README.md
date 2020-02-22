## A script for plotting Strava data

### Getting started
0. Note: the guide below was written for Windows. For other operating systems, another basemap wheel will be required in step 1 of 'Getting started'. Step 2 assumes you're using an Anaconda environment to handle dependencies.
1. Download the basemap-1.2.1-cp36-cp36m-win_amd64.whl file from https://www.lfd.uci.edu/~gohlke/pythonlibs/. (If you're running a 32-bit OS, take basemap‑1.2.1‑cp36‑cp36m‑win32.whl instead, and update environment.yml for that)
2. Run "conda env create --name strava-plotter-env -f environment.yml"
3. Follow section B of the instructions at https://developers.strava.com/docs/getting-started/ to create your personal Strava app.
4. Rename '.env.example' to '.env' and fill the CLIENT_ID, CLIENT_SECRET you obtained in the previous steps, as well as your ATHLETE_ID.

### Running the the script
1. If desired, change the settings in settings.py
2. Run strava_plotter.py from the strava-plotter-env
3. Follow the instructions shown in the console
