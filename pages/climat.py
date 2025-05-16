from nicegui import ui
import requests
import csv

def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,wind_speed_10m&forecast_days=4"
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

def get_region_name(lat, lon):
    url = f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1'
    try:
        resp = requests.get(url, headers={'User-Agent': 'NiceGUI-AgroApp'})
        if resp.status_code == 200:
            data = resp.json()
            return data.get('display_name', 'Неизвестный регион')
    except Exception:
        pass
    return 'Неизвестный регион'

def climat_page():
    ui.label('Климатические данные').classes('text-h4 q-mb-md')
    lat_input = ui.input('Широта', value='55.75').props('type=number step=0.01')
    lon_input = ui.input('Долгота', value='37.62').props('type=number step=0.01')
    region_label = ui.label('Регион: ...').classes('q-mb-md')
    table = ui.table(
        columns=[
            {'name': 'date', 'label': 'Дата', 'field': 'date'},
            {'name': 'temp', 'label': 'Температура', 'field': 'temp'},
            {'name': 'precip', 'label': 'Осадки', 'field': 'precip'},
            {'name': 'wind', 'label': 'Ветер', 'field': 'wind'},
        ],
        rows=[]
    ).classes('w-full')
    weather_data = []

    def update_weather():
        lat = float(lat_input.value)
        lon = float(lon_input.value)
        nonlocal weather_data
        weather_data = get_weather_data(lat, lon)
        table.rows = weather_data
        table.update()
        region = get_region_name(lat, lon)
        region_label.text = f'Регион: {region}'

    def export_csv():
        if not weather_data:
            ui.notify('Нет данных для экспорта', color='warning')
            return
        filename = 'climate_data.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['date', 'temp', 'precip', 'wind'])
            writer.writeheader()
            for row in weather_data:
                writer.writerow(row)
        ui.download(filename)
        ui.notify(f'Данные выгружены в {filename}', color='positive')

    ui.button('Обновить', on_click=update_weather).classes('q-mt-md')
    ui.button('Выгрузить в CSV', on_click=export_csv).classes('q-mt-md') 