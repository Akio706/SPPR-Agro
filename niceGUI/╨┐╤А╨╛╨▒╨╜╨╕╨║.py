def read_geojson():
    counties=json.load(open("chernozem_regions_refixed.geojson", "r"))
    i=0
    for feature in counties["features"]:
        i+