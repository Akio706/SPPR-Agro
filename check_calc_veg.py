import pandas as pd
import json
from datetime import datetime as dt
import numpy as np
import os
import tempfile



file_path2 = "doys_by_months.csv"
doys = pd.read_csv(file_path2)
first_day_of_the_month = doys.iloc[0]
first_day_of_the_month = doys.iloc[0]
last_day_of_the_month = doys.agg({ 'Jan':"count",'Feb':"count",'Mar':"count",'Apr':"count",'May':"count",'Jun':"count",'Jul':"count",'Aug':"count",'Sep':"count",'Oct':"count",'Nov':"count",'Dec':"count"})
last_day_of_the_month.to_json("last_day_of_the_month.json")
first_day_of_the_month.to_json("first_day_of_the_month.json")
last_day_of_the_month.index = range(0,12,1)
first_day_of_the_month.index = range(0,12,1)
file_path3 = "Phenophases.csv"
pheno = pd.read_csv(file_path3)
#с чтением файлов разобрался, все работает


def calc_vegetation_period(variety_type, first_day_of_the_month, last_day_of_the_month, pheno, start_date_input=None):
    # Если дата не предоставлена, используем текущую дату
    if start_date_input is None:
        start_date_input = dt.now().strftime('%Y-%m-%d')
    
    try:
        start_date = dt.strptime(start_date_input, '%Y-%m-%d')
    except ValueError:
        print("Неверный формат даты. Пожалуйста, используйте формат YYYY-MM-DD.")
        return 

    start_date_doy = start_date.timetuple().tm_yday
    end_date_doy = start_date_doy + 90
    #string_prefix = string_prefix +'DOYs:' + str(start_date_doy) + ' Start Date: ' + start_date_string + ' | '
    seeding_date = start_date_doy
    harvest_date = end_date_doy
    days_in_the_month=last_day_of_the_month
    d = pd.Series([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    sdi = ((first_day_of_the_month - seeding_date)/days_in_the_month)
    hdi = ((first_day_of_the_month - harvest_date)/days_in_the_month)
    #print(first_day_of_the_month)
    first_day_of_decade = pd.Series([1,11,21,32,42,50,60,71,82,91,101,111,121,131,141,152,162,
    172,182,192,202,213,223,233,244,254,264,274,284,294,305,315,325,335,345,355,365,366])
    dd = pd.Series([1.0] * len(first_day_of_decade))
    sddi = ((first_day_of_decade - seeding_date)/10)
    hddi = ((first_day_of_decade - harvest_date)/10)  
 

    if(variety_type == 4):
        pheno = pheno.loc[pheno['Variety'] == 'Zolotaya' ]
    else:
        pheno = pheno.loc[pheno['Variety'] == 'Other' ]
    pheno = pheno.iloc[0:10,1:5]
    # print("Pheno")
    # print(pheno)
    if(seeding_date < harvest_date):
        d.loc[(sdi < 0) | (hdi>1)]=0
        dd.loc[(sddi < 0) | (hddi>1)]=0
    if(seeding_date > harvest_date):
        d.loc[(sdi < 0) & (hdi>1)]=0
        dd.loc[(sddi < 0) & (hddi>1)]=0
    d.loc[((sdi > 0) & (sdi < 1))] = sdi.loc[((sdi > 0) & (sdi <1))]
    d.loc[((hdi > 0) & (hdi < 1))] = hdi.loc[((hdi > 0) & (hdi <1))]
    dd.loc[((sddi > 0) & (sddi < 1))] = sddi.loc[((sddi > 0) & (sddi <1))]
    dd.loc[((hddi > 0) & (hddi < 1))] = hddi.loc[((hddi > 0) & (hddi <1))]
    ddf = pd.DataFrame({
        'FOTB': dd,
        'FSTB': dd,
        'FLTB': dd,
        'VPH':  dd
    })
    

    min_row = np.min(ddf[ddf['FOTB'] > 0].index)
    max_row = np.max(ddf[ddf['FOTB'] > 0].index)
    pheno_cor = ddf
    for i in range(min_row, max_row+1):
        pheno_cor.iloc[i,0] = pheno.iloc[i-min_row,0]
        pheno_cor.iloc[i,1] = pheno.iloc[i-min_row,1]
        pheno_cor.iloc[i,2] = pheno.iloc[i-min_row,2]
        pheno_cor.iloc[i,3] = pheno.iloc[i-min_row,3]

    pheno_cor = pheno_cor.assign(GRAIN = pheno_cor['FOTB']*pd.Series(dd))
    pheno_cor = pheno_cor.assign(STEM = pheno_cor['FSTB']*pd.Series(dd))
    pheno_cor = pheno_cor.assign(LEAF = pheno_cor['FLTB']*pd.Series(dd))
    pheno_cor = pheno_cor.assign(PHASE = pheno_cor['VPH']).filter(['GRAIN','STEM','LEAF','PHASE'])
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
        temp_file_path = temp_file.name #именно эту переменную нужно использовать для вызова в дальнейшем
        pheno_cor.to_json(temp_file_path, orient='split')

    print(f"Результат сохранен во временный файл: {temp_file_path}")
    return temp_file_path #временно сохраняет json файл для дальнейшего использования

variety_type = 3
# Используем текущую дату по умолчанию
result = calc_vegetation_period(variety_type, first_day_of_the_month, last_day_of_the_month, pheno)
print(result)

#функция готова, хотя еще можно добавить выбор variety_type и больше ничего












# пример вызова переменной, содер. наш временный json файл
# def save_to_temp_json(pheno_cor):
#     # Создаем временный JSON-файл
#     with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
#         temp_file_path = temp_file.name
#         pheno_cor.to_json(temp_file_path, orient='split')

#     print(f"Результат сохранен во временный файл: {temp_file_path}")
#     return temp_file_path

# def load_from_temp_json(temp_file_path):
#     # Читаем данные из временного JSON-файла
#     loaded_data = pd.read_json(temp_file_path, orient='split')
#     return loaded_data

# # Пример использования
# # Создаем DataFrame
# pheno_cor = pd.DataFrame({
#     'A': [1, 2, 3],
#     'B': [4, 5, 6]
# })

# # Сохраняем DataFrame во временный JSON-файл и получаем путь
# temp_file_path = save_to_temp_json(pheno_cor)

# # Загружаем данные из временного JSON-файла, передавая путь как аргумент
# loaded_data = load_from_temp_json(temp_file_path)

# print("Загруженные данные из временного файла:")
# print(loaded_data)

# # Удаляем временный файл после использования
# os.remove(temp_file_path)