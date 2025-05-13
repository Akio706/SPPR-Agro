# AgroFields NiceGUI

Веб-приложение для агрономов на NiceGUI и SQLAlchemy для управления полями, полигонами и почвенными данными.

## Основные возможности

- Авторизация пользователей (администратор, агроном, помощник)
- Создание, редактирование, удаление и просмотр полей
- Отображение полей и полигонов на карте (Leaflet)
- Экспорт параметров поля (включая почвенные данные с ArcGIS) в CSV
- Генерация PNG с картой и полигоном
- Просмотр полигона в отдельной вкладке с ограничением перемещения
- Интеграция с ArcGIS REST API для получения почвенных параметров

## Запуск

1. Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

2. Запустите приложение:
    ```bash
    python app.py
    ```

3. Откройте в браузере: [http://127.0.0.1:8080](http://127.0.0.1:8080)

## Запуск через Docker

1. Соберите образ:

```bash
docker build -t nicegui-app .
```

2. Запустите контейнер с SQLite (по умолчанию):

```bash
docker run -p 8080:8080 nicegui-app
```

3. Для использования PostgreSQL:
- Запустите PostgreSQL (например, через docker-compose или вручную)
- Передайте переменную окружения DATABASE_URL, например:

```bash
docker run -p 8080:8080 -e DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname nicegui-app
```

## Пример DATABASE_URL для PostgreSQL
```
postgresql+psycopg2://user:password@host:5432/dbname
```

## Структура проекта

- `app.py` — основной код приложения
- `models/` — модели SQLAlchemy
- `niceGUI/` — дополнительные модули и ресурсы
- `polygons.geojson` — экспортированные полигоны
- `geo_app.db`, `map_data.db` — базы данных

## Лицензия

MIT

---

**Автор:** [Akio706](https://github.com/Akio706) 
