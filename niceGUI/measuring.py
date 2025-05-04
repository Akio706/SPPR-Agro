import pandas as pd
import time 
from nicegui import ui
import numpy as np
import json


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
def update_text(clickData, year_type):
    if clickData is None:
        return "Нет данных для отображения"
    else:
        if year_type == "dry":
            s = df[df['id'] == clickData['points'][0]['customdata']]
            #dt1 = s.iloc[0][["tsum5_d19_7","tsum5_d19_8","tsum5_d19_9","tsum5_d19_10","tsum5_d19_11","tsum5_d19_12","tsum5_d19_13","tsum5_d19_14","tsum5_d19_15","tsum5_d19_16","tsum5_d19_17","tsum5_d19_18","tsum5_d19_19",
            #"tsum5_d19_20","tsum5_d19_21","tsum5_d19_22","tsum5_d19_23","tsum5_d19_24","tsum5_d19_25","tsum5_d19_26","tsum5_d19_27","tsum5_d19_28","tsum5_d19_29","tsum5_d19_30"]].reset_index(drop=True)
            #dt2 = s.iloc[0][["tsum10_d19_7","tsum10_d19_8","tsum10_d19_9","tsum10_d19_10","tsum10_d19_11","tsum10_d19_12","tsum10_d19_13","tsum10_d19_14","tsum10_d19_15","tsum10_d19_16","tsum10_d19_17","tsum10_d19_18","tsum10_d19_19",
            #"tsum10_d19_20","tsum10_d19_21","tsum10_d19_22","tsum10_d19_23","tsum10_d19_24","tsum10_d19_25","tsum10_d19_26","tsum10_d19_27","tsum10_d19_28","tsum10_d19_29","tsum10_d19_30"]].reset_index(drop=True)
            dt1 = s.iloc[0][["tsum5_d10_7","tsum5_d10_8","tsum5_d10_9","tsum5_d10_10","tsum5_d10_11","tsum5_d10_12","tsum5_d10_13","tsum5_d10_14","tsum5_d10_15","tsum5_d10_16","tsum5_d10_17","tsum5_d10_18","tsum5_d10_19",
            "tsum5_d10_20","tsum5_d10_21","tsum5_d10_22","tsum5_d10_23","tsum5_d10_24","tsum5_d10_25","tsum5_d10_26","tsum5_d10_27","tsum5_d10_28","tsum5_d10_29","tsum5_d10_30"]].reset_index(drop=True)
            dt2 = s.iloc[0][["tsum10_d10_7","tsum10_d10_8","tsum10_d10_9","tsum10_d10_10","tsum10_d10_11","tsum10_d10_12","tsum10_d10_13","tsum10_d10_14","tsum10_d10_15","tsum10_d10_16","tsum10_d10_17","tsum10_d10_18","tsum10_d10_19",
            "tsum10_d10_20","tsum10_d10_21","tsum10_d10_22","tsum10_d10_23","tsum10_d10_24","tsum10_d10_25","tsum10_d10_26","tsum10_d10_27","tsum10_d10_28","tsum10_d10_29","tsum10_d10_30"]].reset_index(drop=True)
            dt1 = dt1*1.1
            dt2 = dt2*1.1
            dt3 = s.iloc[0][["prcpn_d10_7","prcpn_d10_8","prcpn_d10_9","prcpn_d10_10","prcpn_d10_11","prcpn_d10_12","prcpn_d10_13","prcpn_d10_14","prcpn_d10_15","prcpn_d10_16","prcpn_d10_17","prcpn_d10_18","prcpn_d10_19","prcpn_d10_20",
            "prcpn_d10_21","prcpn_d10_22","prcpn_d10_23","prcpn_d10_24","prcpn_d10_25","prcpn_d10_26","prcpn_d10_27","prcpn_d10_28","prcpn_d10_29","prcpn_d10_30"]].reset_index(drop=True)
            dt3 = dt3*0.75
            datatable = pd.DataFrame({'tsum5':dt1, 'tsum10':dt2,'prcp':dt3/10}).T
        elif year_type == "wet":
            s = df[df['id'] == clickData['points'][0]['customdata']]
            #dt1 = s.iloc[0][["tsum5_d18_7","tsum5_d18_8","tsum5_d18_9","tsum5_d18_10","tsum5_d18_11","tsum5_d18_12","tsum5_d18_13","tsum5_d18_14","tsum5_d18_15","tsum5_d18_16","tsum5_d18_17","tsum5_d18_18","tsum5_d18_19",
            #"tsum5_d18_20","tsum5_d18_21","tsum5_d18_22","tsum5_d18_23","tsum5_d18_24","tsum5_d18_25","tsum5_d18_26","tsum5_d18_27","tsum5_d18_28","tsum5_d18_29","tsum5_d18_30"]].reset_index(drop=True)
            #dt2 = s.iloc[0][["tsum10_d18_7","tsum10_d18_8","tsum10_d18_9","tsum10_d18_10","tsum10_d18_11","tsum10_d18_12","tsum10_d18_13","tsum10_d18_14","tsum10_d18_15","tsum10_d18_16","tsum10_d18_17","tsum10_d18_18","tsum10_d18_19",
            #"tsum10_d18_20","tsum10_d18_21","tsum10_d18_22","tsum10_d18_23","tsum10_d18_24","tsum10_d18_25","tsum10_d18_26","tsum10_d18_27","tsum10_d18_28","tsum10_d18_29","tsum10_d18_30"]].reset_index(drop=True)
            dt1 = s.iloc[0][["tsum5_d10_7","tsum5_d10_8","tsum5_d10_9","tsum5_d10_10","tsum5_d10_11","tsum5_d10_12","tsum5_d10_13","tsum5_d10_14","tsum5_d10_15","tsum5_d10_16","tsum5_d10_17","tsum5_d10_18","tsum5_d10_19",
            "tsum5_d10_20","tsum5_d10_21","tsum5_d10_22","tsum5_d10_23","tsum5_d10_24","tsum5_d10_25","tsum5_d10_26","tsum5_d10_27","tsum5_d10_28","tsum5_d10_29","tsum5_d10_30"]].reset_index(drop=True)
            dt2 = s.iloc[0][["tsum10_d10_7","tsum10_d10_8","tsum10_d10_9","tsum10_d10_10","tsum10_d10_11","tsum10_d10_12","tsum10_d10_13","tsum10_d10_14","tsum10_d10_15","tsum10_d10_16","tsum10_d10_17","tsum10_d10_18","tsum10_d10_19",
            "tsum10_d10_20","tsum10_d10_21","tsum10_d10_22","tsum10_d10_23","tsum10_d10_24","tsum10_d10_25","tsum10_d10_26","tsum10_d10_27","tsum10_d10_28","tsum10_d10_29","tsum10_d10_30"]].reset_index(drop=True)
            dt1 = dt1*0.9
            dt2 = dt2*0.9
            dt3 = s.iloc[0][["prcpn_d10_7","prcpn_d10_8","prcpn_d10_9","prcpn_d10_10","prcpn_d10_11","prcpn_d10_12","prcpn_d10_13","prcpn_d10_14","prcpn_d10_15","prcpn_d10_16","prcpn_d10_17","prcpn_d10_18","prcpn_d10_19","prcpn_d10_20",
            "prcpn_d10_21","prcpn_d10_22","prcpn_d10_23","prcpn_d10_24","prcpn_d10_25","prcpn_d10_26","prcpn_d10_27","prcpn_d10_28","prcpn_d10_29","prcpn_d10_30"]].reset_index(drop=True)
            dt3 = dt3*1.25
            datatable = pd.DataFrame({'tsum5':dt1, 'tsum10':dt2,'prcp':dt3/10}).T
        else:
            s = df[df['id'] == clickData['points'][0]['customdata']]
            dt1 = s.iloc[0][["tsum5_d10_7","tsum5_d10_8","tsum5_d10_9","tsum5_d10_10","tsum5_d10_11","tsum5_d10_12","tsum5_d10_13","tsum5_d10_14","tsum5_d10_15","tsum5_d10_16","tsum5_d10_17","tsum5_d10_18","tsum5_d10_19",
            "tsum5_d10_20","tsum5_d10_21","tsum5_d10_22","tsum5_d10_23","tsum5_d10_24","tsum5_d10_25","tsum5_d10_26","tsum5_d10_27","tsum5_d10_28","tsum5_d10_29","tsum5_d10_30"]].reset_index(drop=True)
            dt2 = s.iloc[0][["tsum10_d10_7","tsum10_d10_8","tsum10_d10_9","tsum10_d10_10","tsum10_d10_11","tsum10_d10_12","tsum10_d10_13","tsum10_d10_14","tsum10_d10_15","tsum10_d10_16","tsum10_d10_17","tsum10_d10_18","tsum10_d10_19",
            "tsum10_d10_20","tsum10_d10_21","tsum10_d10_22","tsum10_d10_23","tsum10_d10_24","tsum10_d10_25","tsum10_d10_26","tsum10_d10_27","tsum10_d10_28","tsum10_d10_29","tsum10_d10_30"]].reset_index(drop=True)
            dt3 = s.iloc[0][["prcpn_d10_7","prcpn_d10_8","prcpn_d10_9","prcpn_d10_10","prcpn_d10_11","prcpn_d10_12","prcpn_d10_13","prcpn_d10_14","prcpn_d10_15","prcpn_d10_16","prcpn_d10_17","prcpn_d10_18","prcpn_d10_19","prcpn_d10_20",
            "prcpn_d10_21","prcpn_d10_22","prcpn_d10_23","prcpn_d10_24","prcpn_d10_25","prcpn_d10_26","prcpn_d10_27","prcpn_d10_28","prcpn_d10_29","prcpn_d10_30"]].reset_index(drop=True)
            
            #Precipitation should be devided by 10 
            datatable = pd.DataFrame({'tsum5':dt1, 'tsum10':dt2,'prcp':dt3/10}).T
            datatable.index
        
        datatable = datatable.clip(lower=0)
        id = ['tsum5','tsum10','prcp']
        #datatable.insert(loc=30,column="id",value = ['tsum5','tsum10','prcp']) 
        datatable['id'] = id
        
        #datatable = 
        #
        #print("Try 3")
        #print(datatable.iloc[0:3, 0:24].set_axis([7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30], axis=1, inplace=False).copy())
        #datatable = datatable.reset_index()
        #print("Raw datatable")
        #print(datatable)
        df2 = datatable.iloc[0:3, 0:24].set_axis([7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30], axis=1, inplace=False).copy()
        #print("Updated datatable")
        #print(df2)
        #print(df2.round(1).to_dict('records'))

    return df2.round(1).to_dict('records')  


#наша основная функция
def calculate_yield(decades_weather, soilbon, variety_type,slope, exposition, PARj, Radiationj, phases_separation, VarConstj, Language):
    
    #at5 = pd.Series([jan_at5, feb_at5, march_at5, apr_at5, may_at5, jun_at5, jul_at5, aug_at5, sep_at5, oct_at5, nov_at5,
    #                dec_at5])-
    
    at5 = pd.to_numeric(pd.DataFrame(decades_weather).iloc[0])
    
    at10 = pd.to_numeric(pd.DataFrame(decades_weather).iloc[1])
    precip = pd.to_numeric(pd.DataFrame(decades_weather).iloc[2])
    b = slope
    void = pd.Series([0,0,0,0,0,0])
    at5_long = void.append(at5).append(void).append(pd.Series([0])).reset_index(drop=True)
    at10_long = void.append(at10).append(void).append(pd.Series([0])).reset_index(drop=True)
    precip_long = void.append(precip).append(void).append(pd.Series([0])).reset_index(drop=True)

    #это input тема
    if exposition == 'S':
        y = 1 + 0.010 * b
    elif exposition == 'N':
        y = 1 - 0.014 * b
    elif exposition == 'WE':
        y = 1
    

    Radiation = pd.read_json(Radiationj, orient='split')
    #Radiation = Radiation / 3 #because it is on decade not month level
    
    phases_separation = pd.read_json(phases_separation, orient='split')
    #print(phases_separation)
    #Qj_1 = pd.read_json(VarConstj, typ='series', orient='split')["Qj1"]
    #Qj_2 = pd.read_json(VarConstj, typ='series', orient='split')["Qj2"]
    #Qj_3 = pd.read_json(VarConstj, typ='series', orient='split')["Qj3"]
    #Qj_4 = pd.read_json(VarConstj, typ='series', orient='split')["Qj4"]
    #Qj_5 = pd.read_json(VarConstj, typ='series', orient='split')["Qj5"]
    Qj = pd.read_json(VarConstj, typ='series', orient='split')
    #print(Qj)
    Lj = pd.read_json(VarConstj, typ='series', orient='split')["Lj"]
    #print(Lj)
    Kj = pd.read_json(VarConstj, typ='series', orient='split')["Kj"]
    #print(Kj)
    Ej = pd.read_json(VarConstj, typ='series', orient='split')["Ej"]
    #print(Ej)
    #print(at5_long)
    #print(Radiation.afi)
    #print(Radiation.bfi)
    #print(y)

    #AFI and BFi берется из coef_dacedes
    F = Radiation.afi / 10/ 3 + Radiation.bfi / 1000 * y * at5_long
    #print(F)
    Fd_grain = F * phases_separation['GRAIN']
    Fd_stem = F * phases_separation['STEM']
    Fd_leaf = F * phases_separation['LEAF']
    #print(Fd_grain)
    #print(Fd_grain.sum())
    Yield_PAR = 1.5*np.around(1000 * ((Kj / (Qj[variety_type] * (100 - Ej))) * Fd_grain.sum() / 10)*soilbon/100,2)
    Yield_PARd = 1.5*np.around(1000 * ((Kj / (Qj[variety_type] * (100 - Ej))) * Fd_grain / 10)*soilbon/100,2)
    #print( Yield_PAR )
    Stem_PAR =  1.5*np.around(1000 * ((Kj / (Qj[variety_type]  * (100 - Ej))) * Fd_stem.sum() / 10)*soilbon/100,2)
    Stem_PARd =  1.5*np.around(1000 * ((Kj / (Qj[variety_type]  * (100 - Ej))) * Fd_stem / 10)*soilbon/100,2)
    #print(Stem_PAR)
    Leaf_PAR =  1.5*np.around(1000 * ((Kj / (Qj[variety_type]  * (100 - Ej))) * Fd_leaf.sum() / 10)*soilbon/100,2)
    Leaf_PARd =  1.5*np.around(1000 * ((Kj / (Qj[variety_type]  * (100 - Ej))) * Fd_leaf / 10)*soilbon/100,2)
    #print(Leaf_PAR)

    Bi = Radiation.Rafi / 10/3 + Radiation.Rbfi / 1000 * y * at10_long
    #print(Bi)
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