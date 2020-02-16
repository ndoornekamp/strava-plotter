from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

map = Basemap(
        llcrnrlon=0,  # Left
        llcrnrlat=43,  # Down
        urcrnrlon=20,  # Right
        urcrnrlat=53,  # Up
        epsg=23095
    )
#Available services listed here: http://server.arcgisonline.com/arcgis/rest/services

map.arcgisimage(service="World_Imagery", xpixels=400, verbose= True)
plt.show()