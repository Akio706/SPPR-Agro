import json
import random

def get_field_advisory(geojson_path='polygons.geojson', field_id=0, ndvi=None, weather=None):
    # Загружаем данные о поле
    with open(geojson_path, encoding='utf-8') as f:
        geojson_data = json.load(f)
    feature = geojson_data['features'][field_id]
    name = feature['properties'].get('name', f'Поле {field_id+1}')

    # Пример простых рекомендаций
    if ndvi is None:
        ndvi = random.uniform(0.2, 0.9)
    if weather is None:
        weather = {'rain': random.uniform(0, 10), 'temp': random.uniform(10, 30)}

    recommendations = []
    if ndvi < 0.4:
        recommendations.append('Внимание: низкий NDVI, рекомендуется проверить состояние посевов.')
    if weather['rain'] < 2:
        recommendations.append('Мало осадков — рекомендуется полив.')
    if weather['temp'] > 28:
        recommendations.append('Высокая температура — возможен стресс растений.')
    if not recommendations:
        recommendations.append('Состояние поля хорошее, специальных действий не требуется.')

    return {
        'field': name,
        'ndvi': round(ndvi, 2),
        'weather': weather,
        'recommendations': recommendations
    } 