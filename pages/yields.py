from nicegui import ui
from db import Session, Field
import requests
import json
from utils import get_arcgis_soil_params
import csv

def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,wind_speed_10m&forecast_days=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temps = data['hourly']['temperature_2m']
        precs = data['hourly']['precipitation']
        winds = data['hourly']['wind_speed_10m']
        avg_temp = sum(temps) / len(temps) if temps else None
        avg_prec = sum(precs) / len(precs) if precs else None
        avg_wind = sum(winds) / len(winds) if winds else None
        return avg_temp, avg_prec, avg_wind
    return None, None, None

def dodonov_formula(area, temp, prec, wind):
    # Урожай = площадь * (0.8*темп + 0.5*осадки - 0.3*ветер)
    return area * (0.8*temp + 0.5*prec - 0.3*wind)

def monteith_formula(area, temp, prec, rad=15):
    # FAO/Монтей: Урожай = площадь * рад * (темп/25) * (осадки/100)
    return area * rad * (temp/25) * (prec/100)

def fao_simple(area, temp, prec):
    # FAO простая: Урожай = площадь * (темп + осадки/10)
    return area * (temp + prec/10)

def yields_page():
    ui.label('Расчёт урожайности').classes('text-h4 q-mb-md')
    session = Session()
    fields = session.query(Field).all()
    session.close()
    field_options = [(f"{f.id}: {f.name}", f.id) for f in fields]
    selected_field = ui.select(field_options, label='Выберите поле по ID').classes('q-mb-md')
    formula = ui.select([
        ('Простая', 'simple'),
        ('Додонов', 'dodonov'),
        ('Монтей (FAO)', 'monteith'),
        ('FAO простая', 'fao'),
    ], value='simple', label='Формула расчёта').classes('q-mb-md')
    result_label = ui.label('').classes('q-mt-md')
    soil_label = ui.label('').classes('q-mt-md')
    export_data = []

    def calculate_yield():
        field_id = selected_field.value
        if not field_id:
            ui.notify('Выберите поле', color='warning')
            return
        field_id = int(field_id)
        session = Session()
        field = session.query(Field).filter(Field.id == field_id).first()
        session.close()
        if not field:
            ui.notify('Поле не найдено', color='negative')
            return
        coords = json.loads(field.coordinates)
        latlng = coords[0][0] if coords and coords[0] else None
        if not latlng:
            ui.notify('Нет координат у поля', color='negative')
            return
        lat, lon = latlng['lat'], latlng['lng']
        avg_temp, avg_prec, avg_wind = get_weather_data(lat, lon)
        area = field.area if field.area else 1
        if avg_temp is not None and avg_prec is not None:
            if formula.value == 'dodonov':
                yield_value = dodonov_formula(area, avg_temp, avg_prec, avg_wind or 0)
                fstr = 'Додонов'
            elif formula.value == 'monteith':
                yield_value = monteith_formula(area, avg_temp, avg_prec)
                fstr = 'Монтей (FAO)'
            elif formula.value == 'fao':
                yield_value = fao_simple(area, avg_temp, avg_prec)
                fstr = 'FAO простая'
            else:
                yield_value = area * (avg_temp + avg_prec/10 - (avg_wind or 0)/10)
                fstr = 'Простая'
            result_label.text = f"Оценка урожайности ({fstr}): {yield_value:.2f} (площадь: {area} га, t={avg_temp:.1f}°C, осадки={avg_prec:.1f}мм, ветер={avg_wind:.1f}м/с)"
            export_data.clear()
            export_data.append({
                'field_id': field_id,
                'formula': fstr,
                'area': area,
                'temp': avg_temp,
                'precip': avg_prec,
                'wind': avg_wind,
                'yield': yield_value
            })
        else:
            result_label.text = "Не удалось получить климатические данные."
        # Soil info
        soil = get_arcgis_soil_params(lat, lon)
        if soil:
            soil_label.text = f"Почва: {soil.get('MUSYM', '')} | {soil.get('MUSYM_DESC', '')} | PH: {soil.get('PHH2O', 'нет данных')}"
        else:
            soil_label.text = "Почвенные параметры не найдены."

    def export_csv():
        if not export_data:
            ui.notify('Нет данных для экспорта', color='warning')
            return
        filename = 'yield_results.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=export_data[0].keys())
            writer.writeheader()
            for row in export_data:
                writer.writerow(row)
        ui.download(filename)
        ui.notify(f'Данные выгружены в {filename}', color='positive')

    def avg_yield_all_fields():
        session = Session()
        fields = session.query(Field).all()
        session.close()
        total_yield = 0
        count = 0
        for field in fields:
            coords = json.loads(field.coordinates)
            latlng = coords[0][0] if coords and coords[0] else None
            if not latlng:
                continue
            lat, lon = latlng['lat'], latlng['lng']
            avg_temp, avg_prec, avg_wind = get_weather_data(lat, lon)
            area = field.area if field.area else 1
            if avg_temp is not None and avg_prec is not None:
                y = area * (avg_temp + avg_prec/10 - (avg_wind or 0)/10)
                total_yield += y
                count += 1
        if count:
            ui.notify(f'Средняя урожайность по всем полям: {total_yield/count:.2f}')
        else:
            ui.notify('Нет данных для расчёта средней урожайности')

    ui.button('Назад', on_click=lambda: ui.run_javascript('window.history.back()')).props('flat color=primary').classes('mb-4')
    ui.button('Рассчитать урожайность', on_click=calculate_yield).classes('q-mt-md')
    ui.button('Выгрузить результат в CSV', on_click=export_csv).classes('q-mt-md')
    ui.button('Средняя урожайность по всем полям', on_click=avg_yield_all_fields).classes('q-mt-md') 