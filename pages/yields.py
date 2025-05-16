from nicegui import ui
from db import Session, Field
import requests
import json

def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,wind_speed_10m&forecast_days=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Берём средние значения за сутки
        temps = data['hourly']['temperature_2m']
        precs = data['hourly']['precipitation']
        winds = data['hourly']['wind_speed_10m']
        avg_temp = sum(temps) / len(temps) if temps else None
        avg_prec = sum(precs) / len(precs) if precs else None
        avg_wind = sum(winds) / len(winds) if winds else None
        return avg_temp, avg_prec, avg_wind
    return None, None, None

def yields_page():
    ui.label('Расчёт урожайности').classes('text-h4 q-mb-md')
    session = Session()
    fields = session.query(Field).all()
    session.close()
    field_options = [(f"{f.id}: {f.name}", f.id) for f in fields]
    selected_field = ui.select(field_options, label='Выберите поле по ID').classes('q-mb-md')
    result_label = ui.label('').classes('q-mt-md')

    def calculate_yield():
        field_id = selected_field.value
        if not field_id:
            ui.notify('Выберите поле', color='warning')
            return
        session = Session()
        field = session.query(Field).filter(Field.id == field_id).first()
        session.close()
        if not field:
            ui.notify('Поле не найдено', color='negative')
            return
        coords = json.loads(field.coordinates)
        # Берём первую точку полигона как примерную координату
        latlng = coords[0][0] if coords and coords[0] else None
        if not latlng:
            ui.notify('Нет координат у поля', color='negative')
            return
        lat, lon = latlng['lat'], latlng['lng']
        avg_temp, avg_prec, avg_wind = get_weather_data(lat, lon)
        # Примерная формула: урожай = площадь * (температура + осадки/10 - ветер/10)
        area = field.area if field.area else 1
        if avg_temp is not None and avg_prec is not None and avg_wind is not None:
            yield_value = area * (avg_temp + avg_prec/10 - avg_wind/10)
            result_label.text = f"Оценка урожайности: {yield_value:.2f} (площадь: {area} га, t={avg_temp:.1f}°C, осадки={avg_prec:.1f}мм, ветер={avg_wind:.1f}м/с)"
        else:
            result_label.text = "Не удалось получить климатические данные."

    ui.button('Рассчитать урожайность', on_click=calculate_yield).classes('q-mt-md') 