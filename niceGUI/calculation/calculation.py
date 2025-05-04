from nicegui import app, ui



def calculation_of_harvest():
    with ui.row().classes("grid grid-cols-3 h-screen"):
        with ui.column().classes("w-full col-span-1"):
            with ui.card().classes('w-full h-full flex flex-col justify-center items-center'):
                ui.markdown('''**Выберите дату**''').classes('text-center')
                selected_date = None # создаем переменную, в которую будем записывать выбранную дату

                def on_select_date(event):
                    nonlocal selected_date  # используем nonlocal, чтобы получить доступ к переменной из внешней функции
                    selected_date = event.value  # записываем выбранную дату в переменную
                    ui.notify(selected_date)  # выводим уведомление с выбранной датой

                ui.date(value='2023-01-01', on_change=on_select_date).classes('w-full h-full')
                result = ui.label().classes('w-400 h-full')
                # ----------------------------------
        with ui.column().classes("w-full col-span-1"):
            with ui.card().classes('w-full h-full flex flex-col justify-center items-center'):
                with ui.row().classes('w-full'):
                    with ui.row().classes('w-full'):
                        ui.label('Выберите сорт пшеницы')
                        list_variety = [
                            'Шелом', 
                            'Солдат', 
                            'Орловчанка',
                        ]
                        
                        selected_variety = None # создаем переменную, в которую будем записывать выбранный элемент

                        def on_select_variety(event):
                            nonlocal selected_variety  # используем nonlocal, чтобы получить доступ к переменной из внешней функции
                            selected_variety = event.value  # записываем выбранный элемент в переменную
                            ui.notify(selected_variety)  # выводим уведомление с выбранным значением

                    with ui.row().classes('w-full'):
                        ui.select(options=list_variety, with_input=True, on_change=on_select_variety)  # передаем функцию on_select в качестве обработчика событий
                # ------------------------------------------------------------
                with ui.row().classes('w-full'):
                    with ui.row().classes('w-full'):
                        ui.label('Выберите экспозицию склона')
                        list_exposition = [
                            'Юго-восток', 
                            'Юго-запад', 
                            'Северо-восток', 
                            'Северо-запад',
                        ]
                        
                        selected_exposition = None # создаем переменную, в которую будем записывать выбранный элемент

                        def on_select_exposition(event):
                            nonlocal selected_exposition  # используем nonlocal, чтобы получить доступ к переменной из внешней функции
                            selected_exposition = event.value  # записываем выбранный элемент в переменную
                            ui.notify(selected_exposition)  # выводим уведомление с выбранным значением

                    with ui.row().classes('w-full'):
                        ui.select(options=list_exposition, with_input=True, on_change=on_select_exposition)  # передаем функцию on_select в качестве обработчика событий
                
            

            # ///////////////////////////////////////////////
            
                with ui.row().classes('w-full'):
                    with ui.row().classes('w-full'):
                        ui.label('Выберите уклон')
                        list_angle = [
                            1, 
                            2, 
                            3, 
                            4,
                        ]
                        
                        selected_angle = None # создаем переменную, в которую будем записывать выбранный элемент

                        def on_select_angle(event):
                            nonlocal selected_angle  # используем nonlocal, чтобы получить доступ к переменной из внешней функции
                            selected_angle = event.value  # записываем выбранный элемент в переменную
                            ui.notify(selected_angle)  # выводим уведомление с выбранным значением
                    with ui.row().classes('w-full'):
                        ui.select(options=list_angle, with_input=True, on_change=on_select_angle)  # передаем функцию on_select в качестве обработчика событий

            # ------------------------------------------------------------
                with ui.row().classes('w-full'):
                    with ui.row().classes('w-full'):
                        ui.label('Выберите тип почв, доминирующий на поле')
                        list_soil = [
                            'Чернозем', 
                            'Каштановые почвы', 
                            'Серые лесные почвы', 
                            'Серые лесно-подзолистые почвы',
                        ]
                        
                        selected_soil = None # создаем переменную, в которую буд
                        
                        def on_select_soil(event):
                            nonlocal selected_soil  # используем nonlocal, чтобы получить доступ к переменной из внешней функции
                            selected_soil = event.value  # записываем выбранный элемент в переменную
                            ui.notify(selected_soil)  # выводим уведомление с выбранным значением

                    with ui.row().classes('w-full'):
                        ui.select(options=list_soil, with_input=True, on_change=on_select_soil)  # передаем функцию on_select в качестве обработчика событий

        with ui.column().classes("w-full col-span-1"):
            with ui.card().classes('w-full h-full flex flex-col justify-center items-center'):
                ui.label('Вывод результата').classes('w-full h-full')
                ui.button('Click me!', on_click=lambda: ui.notify(f"{selected_date}, {selected_variety}, {selected_exposition}, {selected_angle}, {selected_soil}"))



