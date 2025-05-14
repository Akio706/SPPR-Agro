from nicegui import ui
from db import Session, Field
from utils import export_all_fields_to_csv, get_arcgis_soil_params, save_arcgis_data_to_db
from datetime import datetime
import json

def fields_page():
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')
    selected = []

    def logout():
        ui.page.user_id = None
        ui.page.user_role = None
        ui.notify('Вы вышли из аккаунта', type='positive')
        ui.open('/')

    with ui.row().classes('absolute top-0 right-0 z-50 p-4'):
        ui.button('Выйти', on_click=logout).props('color=negative').classes('q-ml-md')

    def on_select(e):
        selected.clear()
        if hasattr(e, 'selected') and e.selected:
            selected.extend(e.selected)

    def edit_selected():
        if not selected:
            ui.notify('Выберите поле для редактирования', type='warning')
            return
        field_id = selected[0]['id']
        ui.open(f'/map?action=edit&fields={field_id}')

    def create_field():
        ui.open('/map?action=create')

    def delete_by_id():
        try:
            field_id = int(delete_id_input.value)
        except (TypeError, ValueError):
            ui.notify('Введите корректный ID', color='warning')
            return
        session = Session()
        field = session.query(Field).filter(Field.id == field_id, Field.user_id == ui.page.user_id).first()
        if not field:
            ui.notify('Поле не найдено', color='negative')
            session.close()
            return
        session.delete(field)
        session.commit()
        session.close()
        ui.notify(f'Поле с id={field_id} удалено', color='positive')
        load_fields()

    def export_params_by_id():
        try:
            field_id = int(export_id_input.value)
        except (TypeError, ValueError):
            ui.notify('Введите корректный ID', color='warning')
            return
        filename = f'field_{field_id}_params.csv'
        session = Session()
        field = session.query(Field).filter(Field.id == field_id, Field.user_id == ui.page.user_id).first()
        session.close()
        if not field:
            ui.notify('Поле не найдено', color='negative')
            return
        coords = json.loads(field.coordinates)
        latlngs = coords[0]
        lat = sum(p['lat'] for p in latlngs) / len(latlngs)
        lng = sum(p['lng'] for p in latlngs) / len(latlngs)
        soil_params = get_arcgis_soil_params(lat, lng)
        save_arcgis_data_to_db(field.id, soil_params)
        fieldnames = [
            'id', 'name', 'created_at', 'coordinates', 'group', 'notes', 'area', 'soil_type', 'soil_ph', 'humus_content', 'soil_texture', 'elevation', 'slope', 'aspect',
            'phh2o_0-5cm_mean', 'ocd_0-30cm_mean', 'clay_0-5cm_mean', 'sand_0-5cm_mean', 'silt_0-5cm_mean', 'cec_0-5cm_mean', 'bdod_0-5cm_mean', 'nitrogen_0-5cm_mean'
        ]
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            import csv
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            row = {
                'id': field.id,
                'name': field.name,
                'created_at': field.created_at,
                'coordinates': field.coordinates,
                'group': field.group,
                'notes': field.notes,
                'area': field.area,
                'soil_type': field.soil_type,
                'soil_ph': field.soil_ph,
                'humus_content': field.humus_content,
                'soil_texture': field.soil_texture,
                'elevation': field.elevation,
                'slope': field.slope,
                'aspect': field.aspect,
            }
            row.update(soil_params)
            writer.writerow(row)
        ui.download(filename)
        ui.notify(f'Параметры поля {field_id} выгружены в {filename}', color='positive')

    def show_by_id():
        try:
            field_id = int(show_id_input.value)
        except (TypeError, ValueError):
            ui.notify('Введите корректный ID', color='warning')
            return
        ui.open(f'/map?action=select&fields={field_id}')

    def load_fields():
        session = Session()
        fields = session.query(Field).filter(Field.user_id == ui.page.user_id).all()
        session.close()
        rows = []
        for field in fields:
            rows.append({
                'id': field.id,
                'name': field.name,
                'created_at': field.created_at,
            })
        fields_table.rows = rows

    session = Session()
    fields = session.query(Field).filter(Field.user_id == ui.page.user_id).all()
    session.close()
    rows = []
    for field in fields:
        rows.append({
            'id': field.id,
            'name': field.name,
            'created_at': field.created_at,
        })

    ui.label('Список полей').classes('text-h5 q-mb-md')
    with ui.row().classes('q-mb-md'):
        ui.button('Создать новое поле', on_click=create_field).props('color=positive').classes('q-mr-md')
        delete_id_input = ui.input(label='ID для удаления').props('type=number').classes('q-mr-md')
        ui.button('Удалить по id', on_click=delete_by_id).props('color=negative').classes('q-mr-md')
        show_id_input = ui.input(label='ID для показа на карте').props('type=number').classes('q-mr-md')
        ui.button('Показать полигон на карте по id', on_click=show_by_id).props('color=primary').classes('q-mr-md')
        export_id_input = ui.input(label='ID для экспорта параметров').props('type=number').classes('q-mr-md')
        ui.button('Выгрузить параметры по ID (CSV)', on_click=export_params_by_id).props('color=secondary')
    fields_table = ui.table(
        columns=[
            {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
            {'name': 'name', 'label': 'Название', 'field': 'name', 'align': 'left'},
            {'name': 'created_at', 'label': 'Создано', 'field': 'created_at', 'align': 'left'},
        ],
        rows=rows,
        row_key='id',
        selection='single',
        on_select=on_select
    ).classes('w-full')
    ui.button('Редактировать выбранное поле', on_click=edit_selected).props('color=primary').classes('mt-2')