params = {
    "margin": 0.2,  # Margin by which bounding boxes are extended (in degrees)
    "ids_to_skip": ['621131153'],  # Activity ID's of activities you wish to leave out of the plots
    "activity_types": ['Ride'],  # Activity types to be included in the plots
    "clustered": True,  # Put clusters of rides in separate subplots
    "first_cluster_only": False,  # Include only the first cluster in your figure
    "output_format": 'image',  # ['bytes', 'image']
    "subplots_in_separate_files": False,
}