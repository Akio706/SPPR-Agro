from nicegui import app, ui

app.add_static_files('/images', 'images')
# ui.image('images/1.png')

def create_card():

    with ui.row().classes("grid grid-cols-3 h-screen"):
        with ui.column().classes("w-full col-span-1"):
            with ui.card().classes('w-full h-full flex flex-col justify-center items-center'):
                ui.image('images/1.png').classes("w-2/3")
                with ui.card_section().classes("w-full flex-1"):
                    ui.markdown('''**Мелодия**''').classes('text-center')
                    ui.markdown('''**Масса 1000 семян:** 31-41''').classes("w-full")
                    ui.markdown('''**Описание урожая:** В среднем – 23 ц / га , в Западно-Сибирском регионе – 24 ц / га''').classes("w-full")
                    ui.markdown('''**Устойчивость к болезням:** Устойчив к полеганию, превышает по этому показателю стандарт до 0,5 балла. Среднеустойчив к засухе. Хлебопекарные качества хорошие. Ценная пшеница. Восприимчив к твердой головне, бурой ржавчине и мучнистой росе; сильновосприимчив к корневым гнилям. В полевых условиях слабо поражался пыльной головней.''').classes("w-full")

        with ui.column().classes("w-full col-span-1"):
            with ui.card().classes('w-full h-full flex flex-col justify-center items-center'):
                ui.image('images/2.png').classes("w-2/3")
                with ui.card_section().classes("w-full flex-1"):
                    ui.markdown('''**Мелодия**''').classes('text-center')
                    ui.markdown('''**Масса 1000 семян:** 31-41''').classes("w-full")
                    ui.markdown('''**Описание урожая:** В среднем – 23 ц / га , в Западно-Сибирском регионе – 24 ц / га''').classes("w-full")
                    ui.markdown('''**Устойчивость к болезням:** Устойчив к полеганию, превышает по этому показателю стандарт до 0,5 балла. Среднеустойчив к засухе. Хлебопекарные качества хорошие. Ценная пшеница. Восприимчив к твердой головне, бурой ржавчине и мучнистой росе; сильновосприимчив к корневым гнилям. В полевых условиях слабо поражался пыльной головней.''').classes("w-full")

        with ui.column().classes("w-full col-span-1"):
            with ui.card().classes('w-full h-full flex flex-col justify-center items-center'):
                ui.image('images/3.png').classes("w-2/3")
                with ui.card_section().classes("w-full flex-1"):
                    ui.markdown('''**Мелодия**''').classes('text-center')
                    ui.markdown('''**Масса 1000 семян:** 31-41''').classes("w-full")
                    ui.markdown('''**Описание урожая:** В среднем – 23 ц / га , в Западно-Сибирском регионе – 24 ц / га''').classes("w-full")
                    ui.markdown('''**Устойчивость к болезням:** Устойчив к полеганию, превышает по этому показателю стандарт до 0,5 балла. Среднеустойчив к засухе. Хлебопекарные качества хорошие. Ценная пшеница. Восприимчив к твердой головне, бурой ржавчине и мучнистой росе; сильновосприимчив к корневым гнилям. В полевых условиях слабо поражался пыльной головней.''').classes("w-full")

    with ui.row().classes("grid grid-cols-3 h-screen"):
        with ui.column().classes("w-full col-span-1"):
            with ui.card().classes('w-full h-full flex flex-col justify-center items-center'):
                ui.image('images/1.png').classes("w-2/3")
                with ui.card_section().classes("w-full flex-1"):
                    ui.markdown('''**Мелодия**''').classes('text-center')
                    ui.markdown('''**Масса 1000 семян:** 31-41''').classes("w-full")
                    ui.markdown('''**Описание урожая:** В среднем – 23 ц / га , в Западно-Сибирском регионе – 24 ц / га''').classes("w-full")
                    ui.markdown('''**Устойчивость к болезням:** Устойчив к полеганию, превышает по этому показателю стандарт до 0,5 балла. Среднеустойчив к засухе. Хлебопекарные качества хорошие. Ценная пшеница. Восприимчив к твердой головне, бурой ржавчине и мучнистой росе; сильновосприимчив к корневым гнилям. В полевых условиях слабо поражался пыльной головней.''').classes("w-full")

        with ui.column().classes("w-full col-span-1"):
            with ui.card().classes('w-full h-full flex flex-col justify-center items-center'):
                ui.image('images/2.png').classes("w-2/3")
                with ui.card_section().classes("w-full flex-1"):
                    ui.markdown('''**Мелодия**''').classes('text-center')
                    ui.markdown('''**Масса 1000 семян:** 31-41''').classes("w-full")
                    ui.markdown('''**Описание урожая:** В среднем – 23 ц / га , в Западно-Сибирском регионе – 24 ц / га''').classes("w-full")
                    ui.markdown('''**Устойчивость к болезням:** Устойчив к полеганию, превышает по этому показателю стандарт до 0,5 балла. Среднеустойчив к засухе. Хлебопекарные качества хорошие. Ценная пшеница. Восприимчив к твердой головне, бурой ржавчине и мучнистой росе; сильновосприимчив к корневым гнилям. В полевых условиях слабо поражался пыльной головней.''').classes("w-full")

        with ui.column().classes("w-full col-span-1"):
            with ui.card().classes('w-full h-full flex flex-col justify-center items-center'):
                ui.image('images/3.png').classes("w-2/3")
                with ui.card_section().classes("w-full flex-1"):
                    ui.markdown('''**Мелодия**''').classes('text-center')
                    ui.markdown('''**Масса 1000 семян:** 31-41''').classes("w-full")
                    ui.markdown('''**Описание урожая:** В среднем – 23 ц / га , в Западно-Сибирском регионе – 24 ц / га''').classes("w-full")
                    ui.markdown('''**Устойчивость к болезням:** Устойчив к полеганию, превышает по этому показателю стандарт до 0,5 балла. Среднеустойчив к засухе. Хлебопекарные качества хорошие. Ценная пшеница. Восприимчив к твердой головне, бурой ржавчине и мучнистой росе; сильновосприимчив к корневым гнилям. В полевых условиях слабо поражался пыльной головней.''').classes("w-full")

















