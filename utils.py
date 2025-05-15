import requests
import json
from datetime import datetime
from db import Session, Field, SoilAnalysis, ClimateData, FieldArcGISData

def get_arcgis_soil_params(lat, lng):
    endpoint = "https://www.ncmhtd.com/arcgis/rest/services/NRCS/NRCS_SoilData/MapServer/4/query"
    params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json"
    }
    try:
        r = requests.get(endpoint, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("features"):
                attrs = data["features"][0]["attributes"]
                return attrs
            else:
                print("Нет данных по данной точке")
                return {}
        else:
            print("Ошибка ArcGIS REST:", r.status_code, r.text)
            return {}
    except Exception as e:
        print("Ошибка запроса к ArcGIS REST:", e)
        return {}

def save_arcgis_data_to_db(field_id, arcgis_data):
    session = Session()
    try:
        record = FieldArcGISData(
            field_id=field_id,
            data=arcgis_data,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(record)
        session.commit()
    except Exception as e:
        print(f"Ошибка при сохранении ArcGIS данных: {e}")
        session.rollback()
    finally:
        session.close()

def export_all_fields_to_csv(user_id, filename):
    try:
        session = Session()
        fields = session.query(Field).filter(Field.user_id == user_id).all()
        session.close()
        if not fields:
            return None
        fieldnames = ['id', 'name', 'created_at', 'coordinates', 'group', 'notes']
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            import csv
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for field in fields:
                writer.writerow({
                    'id': field.id,
                    'name': field.name,
                    'created_at': field.created_at,
                    'coordinates': field.coordinates,
                    'group': field.group,
                    'notes': field.notes
                })
        return filename
    except Exception as e:
        print(f'Ошибка при экспорте в CSV: {e}')
        return None

def geojson_from_coords(coords, name="Поле"):
    # coords: [[lat, lng], ...]
    return {
        "type": "Feature",
        "properties": {"name": name},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[ [lng, lat] for lat, lng in coords ]]
        }
    }

def coords_from_geojson(geojson):
    # geojson: Feature
    # возвращает [[lat, lng], ...]
    coords = geojson["geometry"]["coordinates"][0]
    return [[lat, lng] for lng, lat in coords] 