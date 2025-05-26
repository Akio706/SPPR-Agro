import geopandas as gpd
from shapely.geometry import shape
import json

def check_intersection(user_geometry):
    if isinstance(user_geometry, str):
        geojson = json.loads(user_geometry)
        user_geom = shape(geojson['geometry'])
    else:
        user_geom = user_geometry
    gdf = gpd.read_file('soil_regions_full.gpkg')
    intersected = gdf[gdf.geometry.intersects(user_geom)]
    result = []
    for _, row in intersected.iterrows():
        zone = row.to_dict()
        zone['geometry'] = json.loads(row['geometry'].__geo_interface__)
        result.append(zone)
    return result 