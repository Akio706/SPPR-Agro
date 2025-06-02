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

    # Declare variable for the field info table
    field_info_table = None

    def on_soil_change(e):
        soil_type_state['value'] = e.value
        # Находим бонитет для нового типа почвы из soil_bonitet.csv с учетом схожести
        new_bonitet = find_bonitet_by_soil_type(e.value, bonitet_data)

        # Обновляем значение в поле ввода бонитета
        bonitet_input.value = new_bonitet

        # Форматируем новое значение бонитета для отображения
        new_bonitet_display = new_bonitet if new_bonitet is not None else 'N/A'

        # Обновляем значение бонитета в table_data и обновляем таблицу
        # Находим строку с типом почвы и обновляем ее значение
        if field_info_table and field_info_table.rows:
            for row in field_info_table.rows:
                if isinstance(row, dict) and 'Параметр' in row:
                    if row['Параметр'] == 'Тип почвы / Бонитет':
                        row['Значение'] = f"{soil_type_state['value']} / {new_bonitet_display}"
                        break
        # Обновляем отображение таблицы
        if field_info_table:
            field_info_table.update()

    def on_sort_change(e):
        sort_state['value'] = e.value

    area_ha = poly.area * 111 * 111 if poly else 0

    temp, prec, wind = get_weather_data(sum(p[0] for p in coords_latlng) / len(coords_latlng), sum(p[1] for p in coords_latlng) / len(coords_latlng)) # Fetch once

    with ui.row().classes('w-full'):
        with ui.column().classes('w-2/3'):
            m = ui.leaflet(center=[sum(p[0] for p in coords_latlng) / len(coords_latlng), sum(p[1] for p in coords_latlng) / len(coords_latlng)], zoom=13).classes('h-96 w-full')
            if coords_latlng:
                m.generic_layer(name='polygon', args=[coords_latlng, {'color': 'red', 'weight': 2}])
            soil_geojson_layer = {'layer': None}
            soil_geojson_state = {'visible': False}
            def fetch_and_show_soil_geojson(bounds):
                min_lat = bounds['_southWest']['lat']
                min_lng = bounds['_southWest']['lng']
                max_lat = bounds['_northEast']['lat']
                max_lng = bounds['_northEast']['lng']
                url = f'http://localhost:8080/api/soil_geojson?min_lat={min_lat}&min_lng={min_lng}&max_lat={max_lat}&max_lng={max_lng}'
                import requests
                try:
                    geojson = requests.get(url).json()
                    if soil_geojson_layer['layer']:
                        m.remove_layer(soil_geojson_layer['layer'])
                    soil_geojson_layer['layer'] = m.geo_json(geojson)
                except Exception as ex:
                    ui.notify(f'Ошибка загрузки geojson: {ex}', color='warning')
            def toggle_soil_geojson():
                if not soil_geojson_state['visible']:
                    soil_geojson_state['visible'] = True
                else:
                    soil_geojson_state['visible'] = False
                    if soil_geojson_layer['layer']:
                        m.remove_layer(soil_geojson_layer['layer'])
                        soil_geojson_layer['layer'] = None
            ui.button('Показать карту почв (GeoJSON)', on_click=toggle_soil_geojson).classes('mt-2')
            def on_move_end(e):
                if soil_geojson_state['visible']:
                    fetch_and_show_soil_geojson(e.args['bounds'])
            m.on('moveend', on_move_end)
        with ui.column().classes('w-1/3'):
            with ui.card():
                ui.label('Информация о поле').classes('text-h6')
                initial_bonitet_value = None
                initial_bonitet_source = 'CSV'

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

                initial_bonitet_value = find_bonitet_by_soil_type(soil_type_state['value'], bonitet_data)

                if field.custom_bonitet is not None:
                     initial_bonitet_value = field.custom_bonitet
                     initial_bonitet_source = 'Custom'

                initial_bonitet_display = initial_bonitet_value if initial_bonitet_value is not None else 'N/A'

                table_data = [
                    {'Параметр': 'Название поля', 'Значение': field.name},
                    {'Параметр': 'Площадь (га)', 'Значение': f'{area_ha:.2f}'},
                    {"Параметр": "Тип почвы / Бонитет", "Значение": f"{soil_type_state['value']} / {initial_bonitet_display}"},
                ]
                field_info_table = ui.table(columns=[{'name': 'Параметр', 'label': 'Параметр', 'field': 'Параметр'}, {'name': 'Значение', 'label': 'Значение', 'field': 'Значение'}], rows=table_data).classes('mb-4').props('pagination=5')

                bonitet_input = ui.input(label='Редактировать бонитет', value=initial_bonitet_value).props('type=number').classes('q-mb-md')

                ui.select(all_soil_types, value=soil_type_state['value'], label='Тип почвы', on_change=on_soil_change).classes('q-mb-md')

                def save_changes():
                    session = Session()
                    f = session.query(Field).filter(Field.id == field_id).first()
                    if f:
                        f.soil_type = soil_type_state['value']
                        f.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        try:
                            bonitet_value_to_save = float(bonitet_input.value)
                            f.custom_bonitet = bonitet_value_to_save
                        except (ValueError, TypeError):
                             f.custom_bonitet = None
                             ui.notify('Некорректное значение бонитета. Сохранено как пустое.', color='warning')

                        session.commit()
                        ui.notify('Данные сохранены', color='positive')
                    session.close()
                ui.button('Сохранить', on_click=save_changes).props('color=primary').classes('mt-2')

                # --- Секция информации о сортах ---
                variety_details = {
                    'Аннушка': {
                        'Разработчик': 'ФГБНУ НИИСХ Юго-Востока',
                        'Масса 1000 семян': '41.30 - 47.00',
                        'Потенциальная урожайность': '3.00',
                        'Содержание белка,%': '15.60',
                        'Влажность зерна,%': '9.46',
                        'Масса литра зерна,г': '816.00',
                        'Содержание глютена,%': '30.80',
                        'Индекс глютена': '2.30',
                        'Зольность,%': '67.00',
                        'Стекловидность,%': '1.13',
                        'Черный зародыш,%': '2.32',
                        'Повреждения насекомыми,%': '',
                        'Описание урожая': 'в засушливые годы-1,35 т / га (в среднем по 2007, 2009, 2010, 2012, 2013) в благоприятных - 2,97 т / га (в среднем по 2000, 2003, 2008, 2014, 2015).',
                        'Устойчивость к болезням': 'Сорт Аннушка" практически устойчив к рыхлой головне (Ustilago tritici) и корневым гнилям (Drechslera sorokiniana) вирусным заболеваниям."',
                        'Период вегетации': 'от 98 до 103 дней (полное созревание в первой декаде августа)', # <<< Добавьте эту строку
                    },
                    'Гордея': {
                        'Разработчик': 'ФНЦ БСТ РАН',
                        'Масса 1000 семян': '36.10 - 38.00',
                        'Потенциальная урожайность': '3.20 - 4.00',
                        'Содержание белка,%': '14.90',
                        'Влажность зерна,%': '10.00',
                        'Масса литра зерна,г': '846.00',
                        'Содержание глютена,%': '26.80',
                        'Индекс глютена': '1.66',
                        'Зольность,%': '100.00',
                        'Стекловидность,%': '0.27',
                        'Черный зародыш,%': '0.26',
                        'Повреждения насекомыми,%': '0.15',
                        'Описание урожая': '',
                        'Устойчивость к болезням': 'Сорт Гордея" устойчив к засухе, полеганию и прорастанию на корню. В условиях степной зоны Оренбургской области "Гордея" устойчива к мучнистой росе (Erysiphe graminis), бурой ржавчине (Puccinia triticina) и стеблевой ржавчине (Puccinia graminis f. sp. tritici Erikss). Слабо подверженана пыльной головне (Ustilago tritici)."',
                        'Период вегетации': 'от 252 до 260 дней', # <<< Добавьте эту строку
                    },
                    'Золотая': {
                        'Разработчик': 'Самарский НИИСХ им. Н. М. Тулайкова',
                        'Масса 1000 семян': '41.30',
                        'Потенциальная урожайность': '6.67',
                        'Содержание белка,%': '15.70',
                        'Влажность зерна,%': '10.30',
                        'Масса литра зерна,г': '814.00',
                        'Содержание глютена,%': '26.70',
                        'Индекс глютена': '88.10',
                        'Зольность,%': '2.02',
                        'Стекловидность,%': '100.00',
                        'Черный зародыш,%': '0.50',
                        'Повреждения насекомыми,%': '4.05',
                        'Описание урожая': '1,85 т / га (в среднем по стационарному сортоиспытанию в 2012-2016 гг.)',
                        'Устойчивость к болезням': '"Сорт "Золотая" обладает устойчивостью к мучнистой росе (Erysiphe graminis), темно-бурой пятнистости пшеницы (Drechslera sorokiniana), бурой ржавчине (Puccinia triticina) и стеблевой ржавчине (Puccinia graminis f. sp. secalis Erikss)."',
                        'Период вегетации': 'от 280 до 320 дней', # <<< Добавьте эту строку
                    },
                    'Луч': { # Изменил \"Луч 25\" на \"Луч\" чтобы соответствовать variety_options
                        'Разработчик': 'ФГБНУ НИИСХ Юго-Востока',
                        'Масса 1000 семян': '44.20 - 47.00',
                        'Потенциальная урожайность': '4.26',
                        'Содержание белка,%': '15.90',
                        'Влажность зерна,%': '9.91',
                        'Масса литра зерна,г': '832.00',
                        'Содержание глютена,%': '31.80',
                        'Индекс глютена': '77.80',
                        'Зольность,%': '2.30',
                        'Стекловидность,%': '67.00',
                        'Черный зародыш,%': '1.13',
                        'Повреждения насекомыми,%': '2.32',
                        'Описание урожая': 'в засушливые годы-1,30 т / га (в среднем по 2007, 2009, 2010, 2012, 2013), в благоприятных - 2,97 т / га (в среднем по 2000, 200, 2008, 2014, 2015). В конкурсном испытании института за 2012-2015 годы средняя урожайность составила 2,41 т / га',
                        'Устойчивость к болезням': 'Сорт луч 25 практически устойчив к корневой гнили(Drechslera sorokiniana), слабо поражается вирусными инфекциями, мучнистой росой (Erysiphe graminis), рыхлой головней (Ustilago tritici), практически устойчив к «черному зародышу» зерна.',
                        'Период вегетации': 'Период вегетации пшеницы сорта "Луч" варьируется в зависимости от условий выращивания и региона, но, в среднем, составляет от 90 до 120 дней.'
                    }
                }

                with ui.tabs().classes('w-full mt-4') as tabs:
                    variety_tabs = [ui.tab(variety_name) for variety_name in variety_details.keys()]

                initial_tab_value = field.group if field.group in variety_details.keys() else list(variety_details.keys())[0]

                with ui.tab_panels(tabs, value=initial_tab_value).classes('w-full'):
                    for variety_name, details in variety_details.items():
                        with ui.tab_panel(variety_name):
                            ui.label(f'Информация о сорте: {variety_name}').classes('text-h6')
                            details_table_data = []
                            for param, value in details.items():
                                details_table_data.append({'Параметр': param, 'Значение': value})
                            ui.table(
                                columns=[
                                    {'name': 'Параметр', 'label': 'Параметр', 'field': 'Параметр', 'align': 'left'},
                                    {'name': 'Значение', 'label': 'Значение', 'field': 'Значение', 'align': 'left'},
                                ],
                                rows=details_table_data,
                                row_key='Параметр'
                            ).props('dense flat bordered pagination=5')

    ui.button('Назад', on_click=lambda: ui.navigate.to('/fields')).classes('mt-4')

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
