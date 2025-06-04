from nicegui import ui
from db import Session, Field
import requests
import json
from utils import get_arcgis_soil_params
import csv
import geopandas as gpd
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union
from datetime import datetime
import openpyxl
from openpyxl import Workbook
import pandas as pd
import numpy as np
from measuring import calculate_yield, VarConst, PARj, Radiationj
from check_func_update import update_text
from check_calc_veg import calc_vegetation_period
import tempfile

# Читаем данные бонитета один раз при загрузке модуля
bonitet_data = []
try:
    with open("soil_bonitet.csv", mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                row['bonitet'] = int(row['bonitet'])
            except (ValueError, TypeError):
                row['bonitet'] = None
            if '\ufeffsoil_type' in row:
                row['soil_type'] = row.pop('\ufeffsoil_type')
            bonitet_data.append(row)
except FileNotFoundError:
    print("Error: soil_bonitet.csv not found.")
except Exception as e:
    print(f"Error reading soil_bonitet.csv: {e}")

# Читаем коэффициенты декад
decades_coef = pd.read_csv('coef_decades.csv')

def find_bonitet_by_soil_type(soil_type_name, bonitet_data):
    best_match = None
    best_score = -1
    for row in bonitet_data:
        if row.get('soil_type') and row['soil_type'].strip().lower() == soil_type_name.strip().lower():
            return row.get('bonitet')
    for row in bonitet_data:
        if row.get('soil_type'):
            current_score = 0
            soil_words = soil_type_name.strip().lower().split()
            bonitet_words = row['soil_type'].strip().lower().split()
            for word in soil_words:
                if word in bonitet_words:
                    current_score += 1

            if current_score > best_score:
                best_score = current_score
                best_match = row.get('bonitet')

    return best_match if best_score > 0 else None

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

def read_bonitet_data(filename="soil_bonitet.csv"):
    """Reads bonitet data from a CSV file."""
    bonitet_data = []
    try:
        with open(filename, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert bonitet to integer, handle potential errors
                try:
                    row['bonitet'] = int(row['bonitet'])
                except (ValueError, TypeError):
                    row['bonitet'] = None # Or some default value like 0
                # Remove BOM from the 'soil_type' key if present
                if '\ufeffsoil_type' in row:
                    row['soil_type'] = row.pop('\ufeffsoil_type')
                bonitet_data.append(row)
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return []
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []
    return bonitet_data

def get_field_coords(coords):
    # Если GeoJSON Feature
    if isinstance(coords, dict) and 'geometry' in coords:
        coords_arr = coords['geometry']['coordinates'][0]
        return [[c[1], c[0]] for c in coords_arr]
    # Если список списков (обычно [[{'lat':..., 'lng':...}, ...]])
    if isinstance(coords, list) and len(coords) > 0:
        if isinstance(coords[0], list):
            inner = coords[0]
            # [{'lat':..., 'lng':...}, ...]
            if len(inner) > 0 and isinstance(inner[0], dict):
                return [[float(p['lat']), float(p['lng'])] for p in inner]
            # [[lat, lng], ...]
            if len(inner) > 0 and isinstance(inner[0], (list, tuple)) and len(inner[0]) == 2:
                return [[float(p[0]), float(p[1])] for p in inner]
        # [{'lat':..., 'lng':...}, ...]
        if isinstance(coords[0], dict):
            return [[float(p['lat']), float(p['lng'])] for p in coords]
        # [[lat, lng], ...]
        if isinstance(coords[0], (list, tuple)) and len(coords[0]) == 2:
            return [[float(p[0]), float(p[1])] for p in coords]
    return []

def show_yield_page(field_id: int):
    session = Session()
    field = session.query(Field).filter(Field.id == field_id).first()
    session.close()
    if not field:
        ui.notify('Поле не найдено', color='negative')
        return
    coords = json.loads(field.coordinates)
    coords_latlng = get_field_coords(coords)
    if not coords_latlng or len(coords_latlng) < 3:
        ui.notify('Нет координат у поля', color='negative')
        return
    poly = Polygon([(p[1], p[0]) for p in coords_latlng])
    gdf = gpd.read_file('soil_regions_full.gpkg')
    intersected = gdf[gdf.geometry.intersects(poly)]
    all_soil_types = sorted(set(x for x in gdf['soil_legend_Descript'].dropna().unique().tolist() if x and x.strip()))
    if not intersected.empty:
        soil_type_default = intersected.iloc[0]['soil_legend_Descript']
    else:
        soil_type_default = all_soil_types[0] if all_soil_types else ''
    if field.soil_type and field.soil_type in all_soil_types:
        soil_type_default = field.soil_type
    if soil_type_default and soil_type_default not in all_soil_types:
        all_soil_types.insert(0, soil_type_default)
    soil_type_state = {'value': soil_type_default}
    variety_options = ['Аннушка', 'Гордея', 'Луч', 'Золотая']
    sort_state = {'value': field.group or variety_options[0]}

    # Инициализация переменных для ввода
    bonitet_input = ui.input(label='Бонитет', value=str(field.custom_bonitet or '')).classes('w-full')
    slope_input = ui.input(label='Уклон (%)', value='0').classes('w-full')
    exposition_select = ui.select(
        label='Экспозиция',
        options=['S', 'N', 'WE'],
        value='S'
    ).classes('w-full')
    year_type_select = ui.select(
        label='Тип года',
        options=['normal', 'dry', 'wet'],
        value='normal'
    ).classes('w-full')

    def on_soil_change(e):
        try:
            soil_type_state['value'] = e.value
            new_bonitet = find_bonitet_by_soil_type(e.value, bonitet_data)
            bonitet_input.value = str(new_bonitet) if new_bonitet is not None else ''
            
            if field_info_table and field_info_table.rows:
                for row in field_info_table.rows:
                    if isinstance(row, dict) and row.get('Параметр') == 'Тип почвы / Бонитет':
                        row['Значение'] = f"{soil_type_state['value']} / {new_bonitet or 'N/A'}"
                        break
                field_info_table.update()
        except Exception as e:
            ui.notify(f'Ошибка при обновлении типа почвы: {str(e)}', color='negative')

    def on_sort_change(e):
        try:
            sort_state['value'] = e.value
        except Exception as e:
            ui.notify(f'Ошибка при выборе сорта: {str(e)}', color='negative')

    area_ha = poly.area * 111 * 111 if poly else 0

    try:
        temp, prec, wind = get_weather_data(
            sum(p[0] for p in coords_latlng) / len(coords_latlng),
            sum(p[1] for p in coords_latlng) / len(coords_latlng)
        )
    except Exception as e:
        ui.notify(f'Ошибка при получении погодных данных: {str(e)}', color='warning')
        temp, prec, wind = None, None, None

    with ui.row().classes('w-full'):
        with ui.column().classes('w-2/3'):
            m = ui.leaflet(
                center=[sum(p[0] for p in coords_latlng) / len(coords_latlng),
                       sum(p[1] for p in coords_latlng) / len(coords_latlng)],
                zoom=13
            ).classes('h-96 w-full')
            
            if coords_latlng:
                m.generic_layer(name='polygon', args=[coords_latlng, {'color': 'red', 'weight': 2}])
            
            # Добавляем информацию о сортах
            with ui.card().classes('w-full mt-4'):
                ui.label('Информация о сортах').classes('text-h6')
                
                # Определяем колонки для таблицы сортов
                variety_columns = [
                    {'name': 'sort', 'label': 'Сорт', 'field': 'Сорт', 'align': 'left'},
                    {'name': 'characteristics', 'label': 'Характеристики', 'field': 'Характеристики', 'align': 'left'},
                ]

                # Определяем данные для таблицы сортов
                variety_data = [
                    {'Сорт': 'Аннушка', 'Характеристики': 'Среднеспелый, устойчивый к засухе'},
                    {'Сорт': 'Гордея', 'Характеристики': 'Раннеспелый, высокоурожайный'},
                    {'Сорт': 'Луч', 'Характеристики': 'Среднеспелый, устойчивый к болезням'},
                    {'Сорт': 'Золотая', 'Характеристики': 'Позднеспелый, высококачественное зерно'}
                ]

                # Создаем таблицу, передавая колонки и данные строк
                variety_info = ui.table(
                    columns=variety_columns,
                    rows=variety_data,
                    row_key='Сорт' # Уникальный ключ строки
                ).classes('w-full')

            # Добавляем выбор сорта
            with ui.card().classes('w-full mt-4'):
                ui.label('Выбор сорта').classes('text-h6')
                variety_select = ui.select(
                    label='Выберите сорт',
                    options=variety_options,
                    value=sort_state['value']
                ).classes('w-full')
                variety_select.on('update', on_sort_change)

            # Добавляем информацию о поле
            with ui.card().classes('w-full mt-4'):
                ui.label('Информация о поле').classes('text-h6')

                # Определяем колонки для таблицы информации о поле
                field_info_columns = [
                    {'name': 'parameter', 'label': 'Параметр', 'field': 'Параметр', 'align': 'left'},
                    {'name': 'value', 'label': 'Значение', 'field': 'Значение', 'align': 'left'},
                ]

                # Определяем данные для таблицы информации о поле
                field_info_data = [
                    {'Параметр': 'Площадь', 'Значение': f'{area_ha:.2f} га'},
                    {'Параметр': 'Тип почвы / Бонитет', 'Значение': f"{soil_type_state['value']} / {find_bonitet_by_soil_type(soil_type_state['value'], bonitet_data) or 'N/A'}"},
                    {'Параметр': 'Текущая температура', 'Значение': f'{temp:.1f}°C' if temp else 'N/A'},
                    {'Параметр': 'Осадки', 'Значение': f'{prec:.1f} мм' if prec else 'N/A'},
                    {'Параметр': 'Скорость ветра', 'Значение': f'{wind:.1f} м/с' if wind else 'N/A'}
                ]

                # Создаем таблицу информации о поле
                field_info_table = ui.table(
                    columns=field_info_columns,
                    rows=field_info_data,
                    row_key='Параметр' # Уникальный ключ строки
                ).classes('w-full')

        with ui.column().classes('w-1/3'):
            # Добавляем параметры расчета
            with ui.card().classes('w-full'):
                ui.label('Параметры расчета').classes('text-h6')
                ui.select(
                    label='Тип почвы',
                    options=all_soil_types,
                    value=soil_type_state['value'],
                    on_change=lambda e: on_soil_change(e, bonitet_input, field_info_table, soil_type_state)
                ).classes('w-full')
                bonitet_input.classes('w-full')
                slope_input.classes('w-full')
                exposition_select.classes('w-full')
                year_type_select.classes('w-full')

            # Добавляем кнопку расчета урожайности
            with ui.card().classes('w-full mt-4'):
                ui.button(
                    'Рассчитать урожайность',
                    on_click=lambda: calculate_yield_results(
                        field.id, soil_type_state, sort_state, bonitet_input, slope_input, 
                        exposition_select, year_type_select, coords_latlng, results_table,
                        variety_options, decades_coef, VarConst
                    )
                ).classes('w-full')

            # Добавляем результаты расчета
            with ui.card().classes('w-full mt-4'):
                ui.label('Результаты расчета').classes('text-h6')

                # Определяем колонки для таблицы результатов расчета
                results_columns = [
                    {'name': 'parameter', 'label': 'Параметр', 'field': 'Параметр', 'align': 'left'},
                    {'name': 'value', 'label': 'Значение', 'field': 'Значение', 'align': 'left'},
                ]

                # Создаем таблицу результатов расчета
                results_table = ui.table(
                    columns=results_columns,
                    rows=[] # Инициализируем с пустыми строками
                ).classes('w-full')

    ui.button('Назад', on_click=lambda: ui.navigate.to('/fields')).classes('mt-4')

    # Добавляем кнопку сохранения изменений
    with ui.row().classes('w-full justify-end'):
         ui.button('Сохранить изменения', on_click=lambda: save_changes(field.id, soil_type_state, sort_state, bonitet_input, Session, Field, ui)).classes('mt-4')

def field_climate_page(field_id: int):
    session = Session()
    field = session.query(Field).filter(Field.id == field_id).first()

    session.close()
    if not field:
        ui.notify('Поле не найдено', color='negative')
        return
    coords = json.loads(field.coordinates)
    coords_latlng = get_field_coords(coords)
    if not coords_latlng or len(coords_latlng) < 3:
        ui.notify('Недостаточно точек для построения полигона', color='negative')
        return
    lat_center = sum(p[0] for p in coords_latlng) / len(coords_latlng)
    lng_center = sum(p[1] for p in coords_latlng) / len(coords_latlng)
    poly = Polygon([(p[1], p[0]) for p in coords_latlng])

    gdf = gpd.read_file('soil_regions_full.gpkg')
    intersected = gdf[gdf.geometry.intersects(poly)] if poly else gdf.iloc[[]]
    all_soil_types = sorted(set(x for x in gdf['soil_legend_Descript'].dropna().unique().tolist() if x and x.strip()))
    if not intersected.empty:
        soil_type_default = intersected.iloc[0]['soil_legend_Descript']
    else:
        soil_type_default = all_soil_types[0] if all_soil_types else ''
    if field.soil_type and field.soil_type in all_soil_types:
        soil_type_default = field.soil_type
    if soil_type_default and soil_type_default not in all_soil_types:
        all_soil_types = [soil_type_default] + all_soil_types

    area_ha = poly.area * 111 * 111 if poly else 0  # Грубо для EPSG:4326

    with ui.row().classes('w-full'):
        with ui.column().classes('w-2/3'):
            m = ui.leaflet(center=[lat_center, lng_center], zoom=13).classes('h-96 w-full')
            if coords_latlng:
                m.generic_layer(name='polygon', args=[coords_latlng, {'color': 'red', 'weight': 2}])
        with ui.column().classes('w-1/3'):
            with ui.card().classes('w-full'):
                ui.label('Информация о поле').classes('text-h6')
                table_data = [
                    {'Параметр': 'Название поля', 'Значение': field.name},
                    {'Параметр': 'Площадь (га)', 'Значение': f'{area_ha:.2f}'},
                    {'Параметр': 'Тип почвы', 'Значение': soil_type_default},
                ]
                ui.table(columns=[{'name': 'Параметр', 'label': 'Параметр', 'field': 'Параметр'}, {'name': 'Значение', 'label': 'Значение', 'field': 'Значение'}], rows=table_data).classes('mb-4').props('pagination=5')
            
            with ui.card().classes('w-full mt-4'):
                ui.label('Бонитет почв').classes('text-h6 mt-4')
                bonitet_data = read_bonitet_data()
                bonitet_columns = [
                    {'name': 'soil_type', 'label': 'Тип почвы', 'field': 'soil_type', 'align': 'left', 'sortable': True, 'classes': ''},
                    {'name': 'bonitet', 'label': 'Бонитет', 'field': 'bonitet', 'align': 'left', 'sortable': True, 'classes': ''},
                ]
                # Создаем таблицу бонитетов с поиском и пагинацией
                bonitet_table_climate = ui.table(
                    columns=bonitet_columns,
                    rows=bonitet_data,
                    row_key='soil_type', # Уникальный ключ строки
                    pagination=10 # Пагинация по 10 строк
                ).classes('mb-4').props('style="max-height: 300px; overflow-y: auto;"')

                # Добавляем поле поиска
                ui.input(label='Поиск по типу почвы').bind_value(bonitet_table_climate, 'filter').classes('mb-4')

                # Debugging prints for bonitet data
                print("--- Debugging Bonitet Data ---")
                print(f"Number of rows read: {len(bonitet_data)}")
                if bonitet_data:
                    print("First row data:", bonitet_data[0])
                    print("Last row data:", bonitet_data[-1])
                print("--- End Debugging ---")

    ui.button('Назад', on_click=lambda: ui.navigate.to('/fields')).classes('mt-4')

def calculate_yield_results(field_id, soil_type_state, sort_state, bonitet_input, slope_input, exposition_select, year_type_select, coords_latlng, results_table, variety_options, decades_coef, VarConst):
    try:
        # Get input values
        soilbon = float(bonitet_input.value) if bonitet_input.value else 0
        variety_type = variety_options.index(sort_state['value']) + 1
        slope = float(slope_input.value) if slope_input.value else 0
        exposition = exposition_select.value
        year_type = year_type_select.value

        # Get weather data for the field
        lat = sum(p[0] for p in coords_latlng) / len(coords_latlng)
        lon = sum(p[1] for p in coords_latlng) / len(coords_latlng)
        
        # Get decades weather data
        decades_weather = update_text({'points': [{'customdata': field_id}]}, year_type)
        
        # Calculate vegetation period
        pheno_file = calc_vegetation_period(variety_type, pd.Series([1,32,60,91,121,152,182,213,244,274,305,335]), 
                                          pd.Series([31,59,90,120,151,181,212,243,273,304,334,365]), 
                                          pd.read_csv('Phenophases.csv'))
        
        # Обновляем PARj и Radiationj с учетом коэффициентов из coef_decades.csv
        PARj_updated = pd.DataFrame({
            'id': decades_coef['id'],
            'afi': decades_coef['afi'],
            'bfi': decades_coef['bfi']
        })
        
        Radiationj_updated = pd.DataFrame({
            'id': decades_coef['id'],
            'afi': decades_coef['Rafi'],  # Используем колонку Rafi для радиации
            'bfi': decades_coef['Rbfi']   # Используем колонку Rbfi для радиации
        })
        
        # Calculate yield with updated coefficients
        result = calculate_yield(decades_weather, soilbon, variety_type, slope, exposition, 
                              PARj_updated.to_json(orient='split'), 
                              Radiationj_updated.to_json(orient='split'),
                              pheno_file, VarConst.to_json(orient='split'), 'ru')
        
        # Parse results
        print(f"Result from calculate_yield: {result}") # Отладочный вывод
        results = json.loads(result)
        
        # Update results table
        results_table.rows = [
            {'Параметр': 'Урожай по PAR', 'Значение': f"{results['PAR']:.2f} т/га"},
            {'Параметр': 'Урожай по осадкам', 'Значение': f"{results['PRC']:.2f} т/га"},
            {'Параметр': 'Итоговый урожай', 'Значение': f"{results['FIN']:.2f} т/га"},
            {'Параметр': 'Стебли', 'Значение': f"{results['PAR_S']:.2f} т/га"},
            {'Параметр': 'Листья', 'Значение': f"{results['PAR_L']:.2f} т/га"}
        ]
        results_table.update()
        
    except Exception as e:
        ui.notify(f'Ошибка при расчете: {str(e)}', color='negative')

def save_changes(field_id, soil_type_state, sort_state, bonitet_input, Session, Field, ui):
    try:
        session = Session()
        f = session.query(Field).filter(Field.id == field_id).first()
        if f:
            f.soil_type = soil_type_state['value']
            f.custom_bonitet = float(bonitet_input.value) if bonitet_input.value else None
            f.group = sort_state['value']
            session.commit()
            ui.notify('Изменения сохранены', color='positive')
        session.close()
    except Exception as e:
        ui.notify(f'Ошибка при сохранении изменений: {str(e)}', color='negative')
