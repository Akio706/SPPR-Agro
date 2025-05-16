from nicegui import ui
import requests

def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,wind_speed_10m&forecast_days=3"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        result = []
        for i, dt in enumerate(data['hourly']['time']):
            result.append({
                'date': dt,
                'temp': data['hourly']['temperature_2m'][i],
                'precip': data['hourly']['precipitation'][i],
                'wind': data['hourly']['wind_speed_10m'][i],
            })
        return result
    return []

def climat_page():
    ui.label('Климатические данные').classes('text-h4 q-mb-md')
    lat_input = ui.input('Широта', value='55.75').props('type=number step=0.01')
    lon_input = ui.input('Долгота', value='37.62').props('type=number step=0.01')
    table = ui.table(
        columns=[
            {'name': 'date', 'label': 'Дата', 'field': 'date'},
            {'name': 'temp', 'label': 'Температура', 'field': 'temp'},
            {'name': 'precip', 'label': 'Осадки', 'field': 'precip'},
            {'name': 'wind', 'label': 'Ветер', 'field': 'wind'},
        ],
        rows=[]
    ).classes('w-full')

    def update_weather():
        lat = float(lat_input.value)
        lon = float(lon_input.value)
        weather = get_weather_data(lat, lon)
        table.rows = weather
        table.update()

    ui.button('Обновить', on_click=update_weather).classes('q-mt-md') 