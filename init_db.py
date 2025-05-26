from db import initialize_db
import geopandas as gpd
import psycopg2
import time

DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'
DB_HOST = 'localhost'
DB_PORT = '5432'
TABLE_NAME = 'zones_regions'

# Функция для создания базы и пользователя, если не существует
def ensure_db_and_user():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        conn.close()
        print('База данных и пользователь уже существуют.')
    except Exception as e:
        print('Не удалось подключиться к базе:', e)
        print('Пробую создать пользователя и базу...')
        conn = psycopg2.connect(dbname='template1', user='postgres', password='postgres', host=DB_HOST, port=DB_PORT)
        conn.autocommit = True
        cur = conn.cursor()
        try:
            cur.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';")
        except Exception:
            pass
        try:
            cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")
        except Exception:
            pass
        cur.close()
        conn.close()
        print('Пользователь и база созданы.')
        time.sleep(2)

# Проверяем и создаём базу/пользователя
ensure_db_and_user()

# Чтение GPKG
print('Чтение zones_regions.gpkg...')
gdf = gpd.read_file('zones_regions.gpkg')
columns = [col for col in gdf.columns if col != 'geometry']
fields_sql = ',\n    '.join([f'{col} TEXT' for col in columns])
create_sql = f'''
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    gid SERIAL PRIMARY KEY,
    {fields_sql},
    geom geometry(MultiPolygon, 4326)
);
'''

# Подключение к базе
for i in range(5):
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        break
    except Exception as e:
        print('Ожидание запуска базы данных...')
        time.sleep(2)
else:
    raise Exception('Не удалось подключиться к базе данных!')
cur = conn.cursor()
print('Создание таблицы...')
cur.execute(create_sql)
conn.commit()

# Проверка на дублирование (по уникальному набору атрибутов)
print('Импорт данных...')
for idx, row in gdf.iterrows():
    values = [str(row[col]) if row[col] is not None else None for col in columns]
    wkt = row.geometry.wkt if row.geometry else None
    if wkt:
        placeholders = ', '.join(['%s'] * len(values))
        # Проверяем, есть ли уже такая запись (по всем атрибутам, кроме gid и geom)
        where_clause = ' AND '.join([f"{col} = %s" for col in columns])
        cur.execute(f"SELECT gid FROM {TABLE_NAME} WHERE {where_clause}", values)
        exists = cur.fetchone()
        if not exists:
            sql = f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}, geom) VALUES ({placeholders}, ST_GeomFromText(%s, 4326))"
            cur.execute(sql, values + [wkt])
conn.commit()
cur.close()
conn.close()
print('Импорт завершён!')

if __name__ == "__main__":
    initialize_db()
    print("Структура базы данных успешно создана.") 