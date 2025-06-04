#проверка update_text
import pandas as pd
import time 
from nicegui import ui
import numpy as np
import json
import pprint as pp  
import os


# data = json.load(open('dcc.geojson', "r"))
# df = pd.concat((pd.json_normalize(row) for row in data['features']), axis=0)



file_path="chernozem_regions_cleaned.geojson"
with open(file_path, "r", encoding="utf-8", errors='ignore') as file:
        data = json.load(file)

# Load the data and ensure id is properly handled
df = pd.json_normalize(data['features'])
df.columns = df.columns.str.replace('properties.', '', regex=False)

# Ensure we have an id column
if 'id' not in df.columns:
    # If id is in properties, it might be named differently
    if 'properties.id' in df.columns:
        df['id'] = df['properties.id']
    else:
        # If no id found, create one from the index
        df['id'] = df.index

tsum_columns = df.filter(regex='^tsum10_d10')
tsum_columns = tsum_columns.reset_index(drop=True)
tsum_columns.index = tsum_columns.index + 1
# print(tsum_columns)
first_row_values = tsum_columns.iloc[0]  # Получаем первую строку
# Обновленный способ обработки отсутствующих значений
numeric_values = first_row_values.fillna(0)
numeric_values = numeric_values.astype(float)  # Явно указываем тип данных
# print(numeric_values) # просто вывод

#print(numeric_values.to_string(index=False))  #без индекса и name

# cleaned_values = [float(value) for value in numeric_values]  # Преобразуем в float
# print(cleaned_values) #в виде списка все значения

#Код по вытаскиванию tsum10_d10 готов





#функция рассчитывает/создает decade_weather, а данная хрень нужна для calculate_yeild. df берется из файла barilla( но скорее всего, инфа из файла chernozem_regions_cleaned)
#нужно добавить возможность выбрать какой год
def update_text(clickData, year_type):
    if clickData is None:
        return "Нет данных для отображения"
    else:
        if year_type == "dry":
            s = df[df['id'] == clickData['points'][0]['customdata']]
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
        datatable['id'] = id
        
        df2 = datatable.iloc[0:3, 0:24].set_axis([7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30], axis=1).copy()

    return df2  # Возвращаем DataFrame вместо словаря

# Test case with proper clickData structure
clickData = {
    'points': [{
        'customdata': 1  # Using the first region's id
    }]
}
year_type = "dry"  # или "wet", в зависимости от ваших нужд
result = update_text(clickData, year_type)
print(result)  # Вывод результата

# Инициализация df2 с данными по умолчанию
default_clickData = {
    'points': [{
        'customdata': 1  # Using the first region's id
    }]
}
df2 = update_text(default_clickData, "normal")  # Инициализируем с нормальным годом
  