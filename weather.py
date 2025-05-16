import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OWM_API_KEY = os.getenv('OWM_API_KEY')


def get_weather_for_field(geojson_path='polygons.geojson', field_id=0):
    # Загружаем данные о поле
    with open(geojson_path, encoding='utf-8') as f:
        geojson_data = json.load(f)
    feature = geojson_data['features'][field_id]
    name = feature['properties'].get('name', f'Поле {field_id+1}')
    # Получаем координаты центра поля
    coords = feature['geometry']['coordinates'][0]
    lats = [pt[1] for pt in coords]
    lons = [pt[0] for pt in coords]
    lat = sum(lats) / len(lats)
    lon = sum(lons) / len(lons)

    if not OWM_API_KEY:
        return {'error': 'API ключ OpenWeatherMap не найден. Добавьте OWM_API_KEY в .env'}

    # Запрос к OpenWeatherMap (5 day / 3 hour forecast)
    url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric&lang=ru'
    resp = requests.get(url)
    if resp.status_code != 200:
        return {'error': f'Ошибка запроса к OpenWeatherMap: {resp.text}'}
    data = resp.json()

    # Формируем краткий прогноз на 3 дня (по 1 точке на день)
    forecast = []
    used_dates = set()
    for item in data['list']:
        date = item['dt_txt'].split(' ')[0]
        if date not in used_dates:
            forecast.append({
                'date': date,
                'temp': item['main']['temp'],
                'rain': item.get('rain', {}).get('3h', 0),
                'description': item['weather'][0]['description']
            })
            used_dates.add(date)
        if len(forecast) >= 3:
            break

    return {
        'field': name,
        'lat': lat,
        'lon': lon,
        'forecast': forecast
    } 