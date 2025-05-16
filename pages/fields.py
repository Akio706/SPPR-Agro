from nicegui import ui
from db import Session, Field, SoilAnalysis, ClimateData
import json
from datetime import datetime
import csv

def fields_page():
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')
    selected = []

    # --- Вкладки ---
    with ui.card().classes('w-full mb-4'):
        with ui.tabs().classes('w-full') as tabs:
            ui.tab('Карта', icon='map')
            ui.tab('Урожайность', icon='agriculture')
            ui.tab('Климат', icon='cloud')
        with ui.tab_panels(tabs, value='Карта').classes('w-full'):
            with ui.tab_panel('Карта'):
                ui.label('Здесь будет карта (пустая)').classes('q-mb-md')
            with ui.tab_panel('Урожайность'):
                ui.open('/yields')
            with ui.tab_panel('Климат'):
                ui.open('/climat')

    # Кнопка выхода
    def logout():
        ui.page.user_id = None
        ui.page.user_role = None
        ui.notify('Вы вышли из аккаунта', type='positive')
        ui.open('/')
    ui.button('Выйти', on_click=logout).classes('absolute top-4 right-4 z-50')

    # Кнопка "Создать поле"
    ui.button('Создать поле', on_click=lambda: ui.open('/map?action=create')).props('color=positive').classes('mt-4')

    # Таблица с кнопкой "Редактировать" в каждой строке
    def edit_field(field_id):
        ui.open(f'/map?action=edit&fields={field_id}')

    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
        {'name': 'name', 'label': 'Название', 'field': 'name', 'align': 'left'},
        {'name': 'created_at', 'label': 'Создано', 'field': 'created_at', 'align': 'left'},
        {'name': 'edit', 'label': '', 'field': 'edit', 'align': 'left'},
    ]
    session = Session()
    user_fields = session.query(Field).filter(Field.user_id == ui.page.user_id).all()
    session.close()
    table_rows = []
    for field in user_fields:
        table_rows.append({
            'id': field.id,
            'name': field.name,
            'created_at': field.created_at,
            'edit': '',  # будет заменено на кнопку ниже
        })
    table = ui.table(
        columns=columns,
        rows=table_rows,
        row_key='id',
        selection='single',
    ).classes('w-full')
    # Добавляем кнопки "Редактировать" после создания таблицы
    for i, row in enumerate(table_rows):
        with table.add_slot('body-cell-edit', row['id']):
            ui.button('Редактировать', on_click=lambda r=row: edit_field(r['id'])).props('color=primary')

    # --- Управление по ID ---
    with ui.row().classes('mt-2'):
        id_input = ui.input(label='ID поля').props('type=number').classes('q-mr-md')
        def edit_by_id():
            try:
                field_id = int(id_input.value)
            except (TypeError, ValueError):
                ui.notify('Введите корректный ID', color='warning')
                return
            ui.open(f'/map?action=edit&fields={field_id}')
        ui.button('Редактировать по ID', on_click=edit_by_id).props('color=primary')
        def export_params_by_id():
            try:
                field_id = int(id_input.value)
            except (TypeError, ValueError):
                ui.notify('Введите корректный ID', color='warning')
                return
            session = Session()
            field = session.query(Field).filter(Field.id == field_id, Field.user_id == ui.page.user_id).first()
            session.close()
            if not field:
                ui.notify('Поле не найдено', color='negative')
                return
            filename = f'field_{field_id}_params.csv'
            coords = json.loads(field.coordinates)
            latlngs = coords[0]
            lat = sum(p['lat'] for p in latlngs) / len(latlngs)
            lng = sum(p['lng'] for p in latlngs) / len(latlngs)
            # Здесь можно добавить получение параметров почвы через ArcGIS, если нужно
            fieldnames = [
                'id', 'name', 'created_at', 'coordinates', 'group', 'notes', 'area', 'soil_type', 'soil_ph', 'humus_content', 'soil_texture', 'elevation', 'slope', 'aspect'
            ]
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
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
                writer.writerow(row)
            ui.download(filename)
            ui.notify(f'Параметры поля {field_id} выгружены в {filename}', color='positive')
        ui.button('Выгрузить параметры по ID (CSV)', on_click=export_params_by_id).props('color=secondary')

    # Кнопка "Удалить поле по ID"
    with ui.row().classes('mt-2'):
        delete_id_input = ui.input(label='ID для удаления').props('type=number').classes('q-mr-md')
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
            ui.open('/fields')
        ui.button('Удалить по id', on_click=delete_by_id).props('color=negative')

    # Кнопка "Показать поле по ID"
    with ui.row().classes('mt-2'):
        show_id_input = ui.input(label='ID для показа на карте').props('type=number').classes('q-mr-md')
        def show_by_id():
            try:
                field_id = int(show_id_input.value)
            except (TypeError, ValueError):
                ui.notify('Введите корректный ID', color='warning')
                return
            ui.open(f'/map?action=select&fields={field_id}')
        ui.button('Показать полигон на карте по id', on_click=show_by_id).props('color=primary')

def delete_field(field_id, user_id):
    try:
        session = Session()
        field = session.query(Field).filter(
            Field.id == field_id,
            Field.user_id == user_id
        ).first()
        if not field:
            return False, "Поле не найдено"
        session.query(SoilAnalysis).filter(SoilAnalysis.field_id == field_id).delete()
        session.query(ClimateData).filter(ClimateData.field_id == field_id).delete()
        session.delete(field)
        session.commit()
        return True, "Поле успешно удалено"
    except Exception as e:
        print(f"Ошибка при удалении поля: {e}")
        session.rollback()
        return False, f"Ошибка при удалении поля: {str(e)}"
    finally:
        session.close() 