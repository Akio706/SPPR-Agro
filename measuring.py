import pandas as pd
import time 
from nicegui import ui
import numpy as np
import json
from check_func_update import df2 #наша таблица с декадой


#правильные варианты создания баз данных:
VarConst = pd.Series({'J':2,'Qj1':1600, 'Qj2':1900,'Qj3':1620,'Qj4':1518,'Qj5':2052,'Lj':2.2,'Kj':300,'Ej':25})
#PAR for decades
decades_coef = pd.read_csv('coef_decades.csv')
pheno = pd.read_csv('Phenophases.csv')
PARj = pd.DataFrame({'id': pd.Series(range(12)) + 1,
                    'afi': pd.Series([0, 0, 0, 32.11, 26.31, 25.64, 23.20, 18.73, 16.30, 13.83, 0, 0]),
                    'bfi': pd.Series([0, 0, 0, 11.30, 9.26, 9.03, 8.16, 6.59, 5.73, 4.87, 0, 0]),
                    })
Radiationj = pd.DataFrame({'id': pd.Series(range(12)) + 1,
                          'afi': pd.Series([0, 0, 0, 16.54, 12.30, 12.40, 10.39, 8.07, 6.45, 4.64, 0, 0]),
                          'bfi': pd.Series([0, 0, 0, 17.27, 12.85, 12.95, 10.84, 8.42, 6.74, 4.84, 0, 0]),
                          }) 
d = pd.Series([0, 0, 0, 0.33, 1, 1, 1, 0.32, 0, 0]) 
start_yield = pd.Series([0,0,0,1586048279]) #хз для чего надо, но пусть будет
decade_weather = df2

#функция для создания decades_weather
#вариант для nicegui, но пока наброски
# @ui.page('/example') 
# def example_page():
#     text_label = ui.label('')

#     @ui.button('Click me').on_click(lambda: update_text(text_label))

# def update_text(label):
#     click_data = get_click_data()  # Ваша логика получения данных
#     if click_data is None:
#         label.set_text('Нет данных для отображения')  # Установите текст по умолчанию
#     else:
#         label.set_text(f'Данные: {click_data}')  # Обновите текст с данными





#функция рассчитывает/создает decade_weather, а данная хрень нужна для calculate_yeild. df берется из файла barilla( но скорее всего, инфа из файла chernozem_regions_cleaned)
#нужно добавить возможность выбрать какой год
# функию update_text убрал, так как она исполь в check func


#наша основная функция
def calculate_yield(decades_weather, soilbon, variety_type,slope, exposition, PARj, Radiationj, phases_separation, VarConstj, Language):
    
    #at5 = pd.Series([jan_at5, feb_at5, march_at5, apr_at5, may_at5, jun_at5, jul_at5, aug_at5, sep_at5, oct_at5, nov_at5,
    #                dec_at5])-
    
    at5 = pd.to_numeric(pd.DataFrame(decades_weather).iloc[0])
    
    at10 = pd.to_numeric(pd.DataFrame(decades_weather).iloc[1])
    precip = pd.to_numeric(pd.DataFrame(decades_weather).iloc[2])
    b = slope
    void = pd.Series([0,0,0,0,0,0])
    at5_long = pd.concat([void, at5, void, pd.Series([0])]).reset_index(drop=True)
    at10_long = pd.concat([void, at10, void, pd.Series([0])]).reset_index(drop=True)
    precip_long = pd.concat([void, precip, void, pd.Series([0])]).reset_index(drop=True)

    #это input тема
    if exposition == 'S':
        y = 1 + 0.010 * b
    elif exposition == 'N':
        y = 1 - 0.014 * b
    elif exposition == 'WE':
        y = 1
    
    # Используем StringIO для чтения JSON из строки
    from io import StringIO
    Radiation = pd.read_json(StringIO(Radiationj), orient='split')
    #Radiation = Radiation / 3 #because it is on decade not month level
    
    # Используем StringIO для чтения JSON из строки
    phases_separation = pd.read_json(StringIO(phases_separation), orient='split')
    #print(phases_separation)
    # Используем StringIO для чтения JSON из строки
    VarConst_series = pd.read_json(StringIO(VarConstj), typ='series', orient='split')
    Qj = VarConst_series.filter(regex='^Qj') # Фильтруем только ключи, начинающиеся на 'Qj'
    Lj = VarConst_series["Lj"]
    Kj = VarConst_series["Kj"]
    Ej = VarConst_series["Ej"]
    #print(at5_long)
    #print(Radiation.afi)
    #print(Radiation.bfi)
    #print(y)

    
    F = Radiation.afi / 10/ 3 + Radiation.bfi / 1000 * y * at5_long
    Fd_grain = F * phases_separation['GRAIN']
    Fd_stem = F * phases_separation['STEM']
    Fd_leaf = F * phases_separation['LEAF']
    # Используем строковый ключ для доступа к Qj
    variety_key = f'Qj{variety_type}'
    Yield_PAR = 1.5*np.around(1000 * ((Kj / (Qj[variety_key] * (100 - Ej))) * Fd_grain.sum() / 10)*soilbon/100,2)
    Yield_PARd = 1.5*np.around(1000 * ((Kj / (Qj[variety_key] * (100 - Ej))) * Fd_grain / 10)*soilbon/100,2)
    #print( Yield_PAR )
    Stem_PAR =  1.5*np.around(1000 * ((Kj / (Qj[variety_key]  * (100 - Ej))) * Fd_stem.sum() / 10)*soilbon/100,2)
    Stem_PARd =  1.5*np.around(1000 * ((Kj / (Qj[variety_key]  * (100 - Ej))) * Fd_stem / 10)*soilbon/100,2)
    Leaf_PAR =  1.5*np.around(1000 * ((Kj / (Qj[variety_key]  * (100 - Ej))) * Fd_leaf.sum() / 10)*soilbon/100,2)
    Leaf_PARd =  1.5*np.around(1000 * ((Kj / (Qj[variety_key]  * (100 - Ej))) * Fd_leaf / 10)*soilbon/100,2)
    #print(Leaf_PAR)

    Bi = Radiation.Rafi / 10/3 + Radiation.Rbfi / 1000 * y * at10_long
    E = 1000*Bi/586
    W = 0 * precip_long 
    #print("E/B")
    #print(E)
    #print(W)
    for z in range(37):
        if z == 9:
            W[z] = 0.65*(precip.iloc[1:z].sum()+precip.iloc[34:37].sum())+.85*precip[z]-E[z]
            #print(W[z])
        if 9 < z < 13:
            W[z] = W[z-1] + 0.85 * precip_long[z] -  E[z]
        if 12 < z < 16:
            W[z] = W[z-1] + 0.85 * precip_long[z] - 0.90 * E[z]
        if 15 < z < 19:
            W[z] = W[z-1] + 0.85 * precip_long[z] - 0.70 * E[z]
        if 18 < z < 22:
            W[z] = W[z-1] + 0.85 * precip_long[z] - 0.55 * E[z]
        if 21 < z < 25:
            W[z] = W[z-1] + 0.85 * precip_long[z] - 0.45 * E[z]
        if 24 < z < 28:
            W[z] = W[z-1] + 0.85 * precip_long[z] - 0.70 * E[z]
        if 27 < z < 32:
            W[z] = W[z-1] + 0.85 * precip_long[z] - 0.70 * E[z]
        if z==33:
            W[z] = W[z-1] + 0.85 * precip_long[z] - E[z]
    
    #print(W)
    Var_coef = Qj / Qj.max()
    Yield_precip = 3*np.around(100*(W*phases_separation['GRAIN']*Var_coef[variety_type]).sum() / (Kj  * (100 - Ej))* (soilbon/ 100),3)  # 100 is empirical instead of 100000
    Yield_precipd = 3*np.around(100*(W*phases_separation['GRAIN']*Var_coef[variety_type]) / (Kj  * (100 - Ej))* (soilbon/ 100),3)

    Stem_precip = 3*np.around(100*(W*phases_separation['STEM']*Var_coef[variety_type]).sum() / (Kj  * (100 - Ej))* (soilbon/ 100),3)
    Stem_precipd = 3*np.around(100*(W*phases_separation['STEM']*Var_coef[variety_type]) / (Kj  * (100 - Ej))* (soilbon/ 100),3)

    Leaf_precip = 3*np.around(100*(W*phases_separation['LEAF']*Var_coef[variety_type]).sum() / (Kj  * (100 - Ej))* (soilbon/ 100),3)
    Leaf_precipd = 3*np.around(100*(W*phases_separation['LEAF']*Var_coef[variety_type]) / (Kj  * (100 - Ej))* (soilbon/ 100),3)
    #print("Leaf precipd")
    #print(Leaf_precipd)
    
    Leaf_result = pd.concat([Leaf_precipd, Leaf_PARd], axis=1)
        
    
    #print("LEAF RESULT")
    #print(Leaf_result)
    Stem_result = pd.concat([Stem_precipd, Stem_PARd], axis=1)
        
    #print(Stem_result)
    Yield_result = pd.concat([Yield_precipd, Yield_PARd], axis=1)
        
    print(Yield_result)

    Yield_finald = pd.DataFrame({
        'Leaf':Leaf_result.min(axis=1),
        'Stem':Stem_result.min(axis=1),
        'Yield':Yield_result.min(axis=1)
    })

    '''
    Yield_finald.Leaf = Leaf_result.min(axis=1)
    Yield_finald.Stem = Stem_result.min(axis=1)
    Yield_finald.Yield = Yield_result.min(axis=1)
    '''
    print("FINAL")
    print(Yield_finald)
    Yield_final = Yield_result.min(axis=1).sum()


    Yields = pd.Series({'PAR':Yield_PAR,'PAR_S':Stem_PAR,'PAR_L':Leaf_PAR, 'PRC':Yield_precip, 
                        'PRC_S':Stem_precip, 'PRC_L':Leaf_precip, 'FIN':Yield_final,'TME':time.time()})
    #Updating language of yield output
    UI_language = Language

    Result = Yields.to_json(orient='split')
    #print(decades_weather)
    #print(d)
    #print(Qj)
    #print(variety_type)
    #dbc.Row([
    #    dbc.Col([
            #html.H3("Yield according to obtained PAR:"),
            #html.H4(UI_text.loc['YieldResultRange',UI_language].format(Yields.min(), Yields.max()))   
           # html.H3("Yield according to precipitation limitations:"),
           # html.H4("{} t/ha".format(Yield_precip)),
           # html.H3("Yield according o precipitation and soil type limitations:"),
           # html.H4("{} t/ha".format(Yield_final)),
    #    ], md=12)
    #])
    return Result









#Yield calculation by decade data
#нужно преобразовать под nicegui этот раздел (пробный вариант от нейронки)
with ui.row():
    data_input = ui.textarea(label='Data Table', placeholder='Enter data here...')
    soilbon_input = ui.input(label='Soil Bond', placeholder='Enter soil bond value...')
    variety_type_input = ui.input(label='Variety Type', placeholder='Enter variety type...')
    slope_input = ui.input(label='Slope', placeholder='Enter slope value...')  # Оставляем как input
    expos_input = ui.input(label='Exposition', placeholder='Enter exposition...')
    PAR_input = ui.input(label='PAR', placeholder='Enter PAR value...')
    RadiationDec_input = ui.input(label='Radiation Dec', placeholder='Enter radiation value...')
    starting_separation_phases_input = ui.input(label='Starting Separation Phases', placeholder='Enter phases...')
    variety_const_input = ui.input(label='Variety Const', placeholder='Enter variety constants...')
    language_switch_input = ui.select(label='Language', options=['en', 'ru'], value='en')

    # Кнопка для запуска вычислений
    ui.button('Calculate Yield', on_click=lambda: update_yield())

# Элемент для отображения результатов
yield_decades_output = ui.label('Yield results will be displayed here.')

def update_yield():
    # Получение значений из интерфейса, но по большей части, все значения должны быть в бд
    data = data_input.value
    soilbon = soilbon_input.value
    variety_type = variety_type_input.value
    slope = float(slope_input.value) if slope_input.value else 0.0  # Преобразование в число;  тоже вводится пользователем
    expos = expos_input.value #вводится пользователем
    PAR = PAR_input.value #табличное значение
    RadiationDec = RadiationDec_input.value #табличное значение
    starting_separation_phases = starting_separation_phases_input.value #табличное значение
    variety_const = variety_const_input.value 
    language = language_switch_input.value

    # Выполнение вычислений
    results = calculate_yield(data, soilbon, variety_type, slope, expos, PAR, RadiationDec, starting_separation_phases, variety_const, language)

    # Обновление вывода
    yield_decades_output.set_text(f"Yield PAR: {results['PAR']}, Yield Precipitation: {results['PRC']}, Final Yield: {results['FIN']}")

# Запуск приложения
ui.run()