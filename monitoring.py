import folium
import json
import numpy as np
import rasterio
from rasterio.transform import from_origin
import base64
from io import BytesIO


def generate_fields_map(geojson_path='polygons.geojson'):
    # Загружаем GeoJSON с полигонами полей
    with open(geojson_path, encoding='utf-8') as f:
        geojson_data = json.load(f)

    # Определяем центр карты (по первому полигону)
    first_feature = geojson_data['features'][0]
    coords = first_feature['geometry']['coordinates'][0][0]
    center = [coords[1], coords[0]]

    # Создаём карту
    m = folium.Map(location=center, zoom_start=13)
    # Добавляем слои полей
    folium.GeoJson(geojson_data, name='fields').add_to(m)
    folium.LayerControl().add_to(m)
    return m


def generate_ndvi_map(geojson_path='polygons.geojson', field_id=0):
    # Загружаем GeoJSON
    with open(geojson_path, encoding='utf-8') as f:
        geojson_data = json.load(f)
    feature = geojson_data['features'][field_id]
    coords = feature['geometry']['coordinates'][0][0]
    center = [coords[1], coords[0]]

    # Генерируем искусственный NDVI-растр
    ndvi = np.random.uniform(0.2, 0.9, (100, 100))
    transform = from_origin(center[1]-0.01, center[0]+0.01, 0.0002, 0.0002)

    # Сохраняем в PNG
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(4,4))
    ax.imshow(ndvi, cmap='YlGn')
    ax.axis('off')
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')

    # Создаём карту
    m = folium.Map(location=center, zoom_start=15)
    folium.GeoJson(feature, name='field').add_to(m)
    folium.raster_layers.ImageOverlay(
        image='data:image/png;base64,'+img_base64,
        bounds=[[center[0]-0.01, center[1]-0.01], [center[0]+0.01, center[1]+0.01]],
        opacity=0.6,
        name='NDVI'
    ).add_to(m)
    folium.LayerControl().add_to(m)
    return m


def generate_dem_map(geojson_path='polygons.geojson', field_id=0):
    # Загружаем GeoJSON
    with open(geojson_path, encoding='utf-8') as f:
        geojson_data = json.load(f)
    feature = geojson_data['features'][field_id]
    coords = feature['geometry']['coordinates'][0][0]
    center = [coords[1], coords[0]]

    # Генерируем искусственный DEM-растр
    dem = np.random.uniform(100, 200, (100, 100))
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(4,4))
    ax.imshow(dem, cmap='terrain')
    ax.axis('off')
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')

    # Создаём карту
    m = folium.Map(location=center, zoom_start=15)
    folium.GeoJson(feature, name='field').add_to(m)
    folium.raster_layers.ImageOverlay(
        image='data:image/png;base64,'+img_base64,
        bounds=[[center[0]-0.01, center[1]-0.01], [center[0]+0.01, center[1]+0.01]],
        opacity=0.6,
        name='DEM'
    ).add_to(m)
    folium.LayerControl().add_to(m)
    return m 