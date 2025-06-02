from nicegui import ui
from db import Session, Field, SoilAnalysis, ClimateData
import json
from datetime import datetime
import csv
from pages.yields import show_yield_page
from pages.climat import climat_page
import psycopg2

def fields_page():
    if not getattr(ui.page, 'user_id', None):
        return ui.navigate.to('/')
    selected = []

    # Кнопка выхода
    def logout():
        ui.page.user_id = None
        ui.page.user_role = None
        ui.notify('Вы вышли из аккаунта', type='positive')
        ui.navigate.to('/')
    ui.button('Выйти', on_click=logout).classes('absolute top-4 right-4 z-50')

    # Кнопка "Создать поле"
    ui.button('Создать поле', on_click=lambda: ui.navigate.to('/map?action=create')).props('color=positive').classes('mt-4')

    # Кнопка "Назад"
    ui.button('Назад', on_click=lambda: ui.run_javascript('window.history.back()')).props('flat color=primary').classes('mb-4')

    # Таблица с кнопкой "Редактировать" в каждой строке
    def edit_field(field_id):
        ui.navigate.to(f'/map?action=edit&fields={field_id}')

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
    # Добавляем выпадающее меню с действиями для каждой строки
    for i, row in enumerate(table_rows):
        with table.add_slot('body-cell-edit', row['id']):
            def go_edit(r=row):
                ui.navigate.to(f'/map?action=edit&fields={r["id"]}')
            def go_yield(r=row):
                ui.navigate.to(f'/yields?field_id={r["id"]}')
            def go_show(r=row):
                ui.navigate.to(f'/field_climate?field_id={r["id"]}')
            # Добавляю кнопку "Удалить" с подтверждением
            async def confirm_delete(r=row):
                with ui.dialog() as dialog, ui.card():
                    ui.label('Вы точно хотите удалить поле?')
                    with ui.row():
                        ui.button('Да', on_click=lambda: dialog.submit('yes'))
                        ui.button('Нет', on_click=lambda: dialog.submit('no'))

                result = await dialog

                if result == 'yes':
                    success, message = delete_field(r["id"], ui.page.user_id)
                    if success:
                        ui.notify(f'Поле с id={r["id"]} удалено', color='positive')
                        ui.navigate.to('/fields')
                    else:
                        ui.notify(f'Ошибка при удалении: {message}', color='negative')

            with ui.row().classes('q-gutter-sm'):
                ui.button('Редактировать').props('color=primary flat disabled')
                ui.button('Урожайность', on_click=lambda r=row: go_yield(r)).props('color=secondary flat')
                ui.button('Показать', on_click=lambda r=row: go_show(r)).props('color=positive flat')
                ui.button('Удалить', on_click=lambda r=row: confirm_delete(r)).props('color=negative flat')

    # --- Управление по ID ---
    # УДАЛЯЕМ СЛЕДУЮЩИЕ БЛОКИ КОДА, КОТОРЫЕ ОТВЕЧАЮТ ЗА КНОПКИ ПОД ТАБЛИЦЕЙ:
    # Блок с кнопкой "Редактировать по ID"
    # with ui.row().classes('mt-2'):
    #     id_input = ui.input(label='ID поля').props('type=number').classes('q-mr-md')
    #     def edit_by_id():
    #         try:
    #             field_id = int(id_input.value)
    #         except (TypeError, ValueError):
    #             ui.notify('Введите корректный ID', color='warning')
    #             return
    #         ui.navigate.to(f'/map?action=edit&fields={field_id}')
    #     ui.button('Редактировать по ID', on_click=edit_by_id).props('color=primary')

    # Блок с кнопкой "Выгрузить параметры по ID (CSV)"
    # def export_params_by_id():
    #     # ... (весь код функции export_params_by_id) ...
    # ui.button('Выгрузить параметры по ID (CSV)', on_click=export_params_by_id).props('color=secondary')

    # Блок с кнопкой "Выгрузить зоны (CSV)"
    # def export_zones_to_csv():
    #     # ... (весь код функции export_zones_to_csv) ...
    # ui.button('Выгрузить зоны (CSV)', on_click=export_zones_to_csv).props('color=secondary')

    # Блок с кнопкой "Удалить поле по ID"
    # with ui.row().classes('mt-2'):
    #     delete_id_input = ui.input(label='ID для удаления').props('type=number').classes('q-mr-md')
    #     def delete_by_id():
    #         # ... (весь код функции delete_by_id) ...
    #     ui.button('Удалить по id', on_click=delete_by_id).props('color=negative')

    # Блок с кнопкой "Показать поле по ID" - УДАЛЯЕМ ЭТОТ БЛОК
    # with ui.row().classes('mt-2'):
    #     show_id_input = ui.input(label='ID для показа на карте').props('type=number').classes('q-mr-md')
    #     def show_by_id():
    #         try:
    #             field_id = int(show_id_input.value)
    #         except (TypeError, ValueError):
    #             ui.notify('Введите корректный ID', color='warning')
    #             return
    #         ui.navigate.to(f'/map?action=select&fields={field_id}')
    #     ui.button('Показать полигон на карте по id', on_click=show_by_id).props('color=primary')


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