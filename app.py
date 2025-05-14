from nicegui import binding, events, ui
from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import json
import uuid
import os
import math
import asyncio
import csv
import requests
import folium

# Модели ORM
Base = declarative_base()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://agro:agro_pass@db:5432/agrofields')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Создание таблиц, если их нет
Base.metadata.create_all(engine)

class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default='agronomist')  # administrator, agronomist, assistant
    email = Column(String, unique=True)
    created_at = Column(String, nullable=False)
    last_login = Column(String)
    markers = relationship("Marker", back_populates="user")
    polygons = relationship("Polygon", back_populates="user")
    fields = relationship("Field", back_populates="user")


class Marker(Base):
    __tablename__ = 'marker_coords'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    lat = Column(Float)
    lng = Column(Float)
    user = relationship("User", back_populates="markers")


class Polygon(Base):
    __tablename__ = 'polygon_coords'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    coords = Column(Text)
    user = relationship("User", back_populates="polygons")
    points = relationship("PolygonPoint", back_populates="polygon")


class PolygonPoint(Base):
    __tablename__ = 'polygon_coordsv2'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    lat = Column(Float)
    lng = Column(Float)
    polygon_id = Column(Integer, ForeignKey('polygon_coords.id'))
    polygon = relationship("Polygon", back_populates="points")


class Field(Base):
    __tablename__ = 'fields'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    name = Column(String, nullable=False)
    coordinates = Column(Text, nullable=False)
    area = Column(Float)  # площадь в гектарах
    soil_type = Column(String)  # тип почвы
    soil_ph = Column(Float)  # pH почвы
    humus_content = Column(String)  # содержание гумуса
    soil_texture = Column(String)  # механический состав почвы
    elevation = Column(Float)  # высота над уровнем моря
    slope = Column(Float)  # уклон
    aspect = Column(String)  # экспозиция склона
    created_at = Column(String, nullable=False)
    last_updated = Column(String)
    group = Column(String)  # группировка полей
    notes = Column(Text)  # заметки
    user = relationship("User", back_populates="fields")
    soil_analyses = relationship("SoilAnalysis", back_populates="field")
    climate_data = relationship("ClimateData", back_populates="field")


class SoilAnalysis(Base):
    __tablename__ = 'soil_analyses'
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('fields.id'))
    analysis_date = Column(String, nullable=False)
    ph_value = Column(Float)
    humus_percentage = Column(Float)
    nitrogen_content = Column(Float)
    phosphorus_content = Column(Float)
    potassium_content = Column(Float)
    texture_class = Column(String)
    organic_matter = Column(Float)
    field = relationship("Field", back_populates="soil_analyses")


class ClimateData(Base):
    __tablename__ = 'climate_data'
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('fields.id'))
    date = Column(String, nullable=False)
    temperature = Column(Float)
    precipitation = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    solar_radiation = Column(Float)
    field = relationship("Field", back_populates="climate_data")


class FieldArcGISData(Base):
    __tablename__ = 'field_arcgis_data'
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('fields.id'))
    data = Column(JSON)  # Сохраняем все атрибуты как JSON
    created_at = Column(String, nullable=False)
    field = relationship("Field", backref="arcgis_data")


class MapPolygon:
    coords = binding.BindableProperty()

    def __init__(self):
        self.coords = ""
        self.latlng = ""
        self.latlngs = ""


map_polygon = MapPolygon()


def handle_draw(e: events.GenericEventArguments, user_id):
    layer_type = e.args['layerType']
    coords = e.args['layer'].get('_latlng') or e.args['layer'].get('_latlngs')
    if not coords:
        if '_latlng' in e.args['layer']:
            coords = e.args['layer']['_latlng']
        elif '_latlngs' in e.args['layer']:
            coords = e.args['layer']['_latlngs']
    store_draw(coords, layer_type, user_id)
    ui.notify(f'Drawn a {layer_type} at {coords}')


def store_draw(coords, layer_type, user_id):
    try:
        session = Session()
        if layer_type == 'marker':
            marker = Marker(user_id=user_id,
                            lat=coords['lat'], lng=coords['lng'])
            session.add(marker)
        elif layer_type == 'polygon':
            polygon = Polygon(user_id=user_id, coords=json.dumps(coords))
            session.add(polygon)
            session.flush()  # Получаем ID полигона
            polygon_id = polygon.id

            for point in coords[0]:  # coords is a list of lists
                point_obj = PolygonPoint(
                    user_id=user_id, lat=point['lat'], lng=point['lng'], polygon_id=polygon_id)
                session.add(point_obj)

        session.commit()
        session.close()
        print(f"Coordinates {coords} stored successfully in map_data.db.")
    except Exception as e:
        print(
            f"An error occurred while storing coordinates in map_data.db: {e}")


def export_coords_from_db(user_id):
    try:
        session = Session()
        polygon_results = session.query(Polygon).filter(
            Polygon.user_id == user_id).all()
        session.close()

        print(f"Из БД получены данные: {polygon_results}")

        polygons = []
        for row in polygon_results:
            polygons.append({
                'id': row.id,
                'coords': json.loads(row.coords)
            })

        print(f"Сформированные полигоны: {polygons}")
        return polygons
    except Exception as e:
        print(f"Ошибка при экспорте координат: {e}")
        return []


def add_exported_coords_to_map(user_id, map_id):
    session = Session()
    polygons = session.query(Polygon).filter(Polygon.user_id == user_id).all()
    polygons_data = []
    for polygon in polygons:
        points = session.query(PolygonPoint).filter(
            PolygonPoint.polygon_id == polygon.id
        ).order_by(PolygonPoint.id).all()
        latlngs = [[point.lat, point.lng] for point in points]
        if latlngs and latlngs[0] != latlngs[-1]:
            latlngs.append(latlngs[0])
        polygons_data.append({
            'id': polygon.id,
            'points': latlngs
        })
    session.close()

    if polygons_data:
        polygons_json = json.dumps(polygons_data)
        ui.run_javascript(f'''
            window.mapInstances = window.mapInstances || {{}};
            document.addEventListener('leaflet_map_ready_{map_id}', function() {{
                try {{
                    const map = window.mapInstances['{map_id}'];
                    if (map) {{
                        const polygonsData = {polygons_json};
                        polygonsData.forEach(function(polygon) {{
                            L.polygon(polygon.points, {{
                                color: 'red',
                                weight: 2,
                                opacity: 0.7,
                                fillOpacity: 0.3,
                                id: 'polygon_' + polygon.id
                            }}).addTo(map);
                        }});
                    }}
                }} catch(e) {{
                    console.error("Ошибка при добавлении полигонов:", e);
                }}
            }}, {{ once: true }});
        ''')
    ui.notify('Полигоны успешно добавлены на карту', color='positive')

# Функция для загрузки локальной карты


def load_local_map(map_id, map_file):
    try:
        if not os.path.exists(map_file):
            ui.notify(f'Файл карты {map_file} не найден', color='negative')
            return False

        with open(map_file, 'r') as f:
            geojson_data = json.load(f)

        if 'features' not in geojson_data:
            ui.notify('Некорректный формат GeoJSON', color='negative')
            return False

        # Преобразуем данные для передачи в JavaScript
        geojson_str = json.dumps(geojson_data)

        # Очищаем старые полигоны и добавляем GeoJSON
        ui.run_javascript(f'''
            // Убедимся, что переменная существует
            window.mapInstances = window.mapInstances || {{}};
            
            // Используем событие для обеспечения готовности карты
            document.addEventListener('leaflet_map_ready_{map_id}', function() {{
                try {{
                    const map = window.mapInstances['{map_id}'];
                    if (map) {{
                        console.log("Загрузка GeoJSON через ID карты:", '{map_id}');
                        
                        // Удаляем старые полигоны GeoJSON
                        map.eachLayer(function(layer) {{
                            if (layer instanceof L.Polygon) {{
                                map.removeLayer(layer);
                            }}
                        }});
                        
                        // Добавляем новый GeoJSON
                        const geojsonData = {geojson_str};
                        L.geoJSON(geojsonData, {{
                            style: function(feature) {{
                                return {{
                                    color: 'blue',
                                    weight: 2,
                                    opacity: 0.7,
                                    fillOpacity: 0.3
                                }};
                            }},
                            onEachFeature: function(feature, layer) {{
                                if (feature.properties && feature.properties.id) {{
                                    layer.id = 'polygon_' + feature.properties.id;
                                }}
                                if (feature.properties && feature.properties.name) {{
                                    layer.bindPopup(feature.properties.name);
                                }}
                            }}
                        }}).addTo(map);
                        
                        console.log("GeoJSON успешно загружен");
                    }} else {{
                        console.error("Карта не найдена для загрузки GeoJSON, ID:", '{map_id}');
                    }}
                }} catch(e) {{
                    console.error("Ошибка при загрузке GeoJSON:", e);
                }}
            }}, {{ once: true }});
            
            // Пытаемся сразу выполнить операцию, если карта уже готова
            if (window.mapInstances && window.mapInstances['{map_id}']) {{
                try {{
                    const map = window.mapInstances['{map_id}'];
                    console.log("Карта уже доступна, загрузка GeoJSON");
                    
                    // Удаляем старые полигоны GeoJSON
                    map.eachLayer(function(layer) {{
                        if (layer instanceof L.Polygon) {{
                            map.removeLayer(layer);
                        }}
                    }});
                    
                    // Добавляем новый GeoJSON
                    const geojsonData = {geojson_str};
                    L.geoJSON(geojsonData, {{
                        style: function(feature) {{
                            return {{
                                color: 'blue',
                                weight: 2,
                                opacity: 0.7,
                                fillOpacity: 0.3
                            }};
                        }},
                        onEachFeature: function(feature, layer) {{
                            if (feature.properties && feature.properties.id) {{
                                layer.id = 'polygon_' + feature.properties.id;
                            }}
                            if (feature.properties && feature.properties.name) {{
                                layer.bindPopup(feature.properties.name);
                            }}
                        }}
                    }}).addTo(map);
                    
                    console.log("GeoJSON успешно загружен");
                }} catch(e) {{
                    console.error("Ошибка при прямой загрузке GeoJSON:", e);
                }}
            }} else {{
                console.log("Карта не готова, GeoJSON будет загружен после инициализации");
                // Имитируем событие, если оно еще не произошло
                // document.dispatchEvent(new CustomEvent('leaflet_map_ready_{map_id}'));
            }}
        ''')

        ui.notify(f'Карта успешно загружена из {map_file}', color='positive')
        return True
    except Exception as e:
        print(f"Ошибка при загрузке локальной карты: {e}")
        ui.notify(f'Ошибка при загрузке карты: {str(e)}', color='negative')
        return False

# Функция для экспорта координат полигонов в GeoJSON формат


def export_to_geojson(user_id, filename="polygons.geojson"):
    try:
        session = Session()
        polygon_results = session.query(Polygon).filter(
            Polygon.user_id == user_id).all()
        session.close()

        if not polygon_results:
            ui.notify('Нет данных для экспорта', color='negative')
            return False

        features = []

        for polygon in polygon_results:
            coords_data = json.loads(polygon.coords)

            # Проверяем, что координаты полигона замкнуты
            if coords_data[0][0] != coords_data[0][-1]:
                coords_data[0].append(coords_data[0][0])

            # Преобразуем формат координат для GeoJSON (lng, lat)
            coords_converted = [[[point['lng'], point['lat']]
                                 for point in coords_data[0]]]

            feature = {
                "type": "Feature",
                "properties": {
                    "id": polygon.id
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": coords_converted
                }
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        with open(filename, 'w') as f:
            json.dump(geojson, f)

        ui.notify(
            f'Данные успешно экспортированы в {filename}', color='positive')
        return True
    except Exception as e:
        print(f"Ошибка при экспорте в GeoJSON: {e}")
        ui.notify('Ошибка при экспорте данных', color='negative')
        return False

# Функция для выделения полигона другим цветом


def highlight_polygon(polygon_id, user_id, map_id):
    try:
        # Преобразуем polygon_id в целое число
        polygon_id = int(polygon_id)

        session = Session()
        polygon_coords = session.query(PolygonPoint).filter(
            PolygonPoint.polygon_id == polygon_id,
            PolygonPoint.user_id == user_id
        ).all()
        session.close()

        print(
            f"Найдено точек для полигона #{polygon_id}: {len(polygon_coords)}")

        if polygon_coords:
            # Создаем список координат полигона в формате [[lng, lat], ...]
            latlngs = [[point.lng, point.lat] for point in polygon_coords]
            if latlngs[0] != latlngs[-1]:
                latlngs.append(latlngs[0])
            print(f"Координаты для выделения полигона #{polygon_id}: {latlngs}")
            points_json = json.dumps(latlngs)

            # Вызываем JavaScript для выделения полигона
            ui.run_javascript(f'''
                window.mapInstances = window.mapInstances || {{}};
                document.addEventListener('leaflet_map_ready_{map_id}', function() {{
                    try {{
                        const map = window.mapInstances['{map_id}'];
                        if (map) {{
                            console.log("Вызван highlight_polygon для ID:", '{polygon_id}');
                            map.eachLayer(function(layer) {{
                                if (layer._highlight === true) {{
                                    map.removeLayer(layer);
                                }}
                            }});
                            const points = {points_json};
                            console.log("Точки для выделения:", points);
                            // Рисуем polyline
                            const highlightedPolyline = L.polyline(points, {{
                                color: 'red',
                                weight: 5,
                                opacity: 1,
                                id: 'highlight_polyline_{polygon_id}'
                            }});
                            highlightedPolyline._highlight = true;
                            highlightedPolyline.addTo(map);
                            map.fitBounds(highlightedPolyline.getBounds());
                            // Добавляем маркеры в вершины
                            points.forEach(function(pt) {{
                                L.circleMarker(pt, {{radius: 7, color: 'red', fillColor: 'yellow', fillOpacity: 1}}).addTo(map);
                            }});
                            console.log("Полигон #{polygon_id} выделен polyline и маркерами");
                        }}
                    }} catch(e) {{
                        console.error("Ошибка при выделении полигона:", e);
                    }}
                }}, {{ once: true }});
                if (window.mapInstances && window.mapInstances['{map_id}']) {{
                    try {{
                        const map = window.mapInstances['{map_id}'];
                        map.eachLayer(function(layer) {{
                            if (layer._highlight === true) {{
                                map.removeLayer(layer);
                            }}
                        }});
                        const points = {points_json};
                        console.log("Точки для выделения:", points);
                        const highlightedPolyline = L.polyline(points, {{
                            color: 'red',
                            weight: 5,
                            opacity: 1,
                            id: 'highlight_polyline_{polygon_id}'
                        }});
                        highlightedPolyline._highlight = true;
                        highlightedPolyline.addTo(map);
                        map.fitBounds(highlightedPolyline.getBounds());
                        points.forEach(function(pt) {{
                            L.circleMarker(pt, {{radius: 7, color: 'red', fillColor: 'yellow', fillOpacity: 1}}).addTo(map);
                        }});
                        console.log("Полигон #{polygon_id} выделен polyline и маркерами");
                    }} catch(e) {{
                        console.error("Ошибка при прямом выделении полигона:", e);
                    }}
                }}
            ''')

            ui.notify(f'Полигон #{polygon_id} выделен')
        else:
            ui.notify(
                f'Недостаточно точек для отображения полигона #{polygon_id}', color='negative')
    except Exception as e:
        print(f"Ошибка при выделении полигона: {e}")
        ui.notify(f'Ошибка при выделении полигона: {e}', color='negative')


draw_control = {
    'draw': {
        'polygon': True,
        'marker': True,
        'circle': True,
        'rectangle': True,
        'polyline': True,
        'circlemarker': True,
    },
    'edit': {
        'edit': True,
        'remove': True,
    },
}

# Initialize the database with users table


def initialize_db():
    try:
        Base.metadata.create_all(engine)
        print("База данных успешно инициализирована.")
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")

# A simple user authentication mechanism for demonstration


def authenticate_user(username, password):
    """Аутентификация пользователя"""
    try:
        session = Session()
        user = session.query(User).filter(
            User.username == username, 
            User.password == password
        ).first()
        result = None
        if user:
            # Обновляем время последнего входа
            user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session.commit()
            # Сохраняем нужные данные до закрытия сессии
            result = {
                'user_id': user.user_id,
                'role': user.role,
                'username': user.username
            }
        session.close()
        return result
    except Exception as e:
        print(f"Ошибка при аутентификации пользователя: {e}")
        return None

def register_user(username, password, email, role='agronomist'):
    """Регистрация нового пользователя"""
    try:
        session = Session()
        
        # Проверяем существование пользователя
        existing_user = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            session.close()
            return False, "Пользователь с таким именем или email уже существует"
        
        # Создаем нового пользователя
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            username=username,
            password=password,  # В реальном приложении нужно хешировать пароль
            email=email,
            role=role,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        session.add(user)
        session.commit()
        session.close()
        return True, "Регистрация успешна"
    except Exception as e:
        print(f"Ошибка при регистрации пользователя: {e}")
        return False, f"Ошибка при регистрации: {str(e)}"


# Placeholder to store the current logged-in user's ID
current_user_id = None


@ui.page('/')
def main_page():
    def login(username, password):
        if not username or not password:
            ui.notify('Имя пользователя и пароль не могут быть пустыми', type='warning')
            return
        user = authenticate_user(username, password)
        if user:
            ui.page.user_id = user['user_id']
            ui.page.user_role = user['role']
            ui.notify(f'Добро пожаловать, {username}!', type='positive')
            with ui.row():
                ui.link('Карта полей', '/map').classes('mt-4')
                ui.link('Управление полями', '/fields').classes('mt-4')
                if user['role'] == 'administrator':
                    ui.link('Управление пользователями', '/users').classes('mt-4')
                ui.link('Аналитика', '/analytics').classes('mt-4')
        else:
            ui.notify('Неверное имя пользователя или пароль', type='negative')

    def register(username, password, email):
        if not username or not password or not email:
            ui.notify('Все поля должны быть заполнены', type='warning')
            return
        if len(password) < 8:
            ui.notify('Пароль должен содержать минимум 8 символов', type='warning')
            return
        success, message = register_user(username, password, email)
        if success:
            ui.notify(message, type='positive')
        else:
            ui.notify(message, type='negative')

    with ui.card().classes('w-96 mx-auto mt-20'):
        ui.label('Вход в систему').classes('text-h4 q-mb-md')
        with ui.tabs().classes('w-full') as tabs:
            ui.tab('Вход')
            ui.tab('Регистрация')
        with ui.tab_panels(tabs, value='Вход').classes('w-full'):
            with ui.tab_panel('Вход'):
                login_username = ui.input(label='Имя пользователя').classes('w-full q-mb-md')
                login_password = ui.input(label='Пароль', password=True).classes('w-full q-mb-md')
                ui.button('Войти', on_click=lambda: login(login_username.value, login_password.value)).classes('w-full')
            with ui.tab_panel('Регистрация'):
                reg_username = ui.input(label='Имя пользователя').classes('w-full q-mb-md')
                reg_email = ui.input(label='Email').classes('w-full q-mb-md')
                reg_password = ui.input(label='Пароль', password=True).classes('w-full q-mb-md')
                ui.button('Зарегистрироваться', on_click=lambda: register(reg_username.value, reg_password.value, reg_email.value)).classes('w-full')


@ui.page('/map')
def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')

    map_view = ui.leaflet(center=(51.505, -0.09), zoom=9, draw_control=True).classes('h-96 w-full')

    if action == 'create':
        def handle_field_creation(e: events.GenericEventArguments):
            print('handle_field_creation вызван!')
            ui.notify('Событие draw:created сработало!', type='info')
            print('draw:created event:', e.args)
            coords = None
            if '_latlngs' in e.args['layer']:
                coords = e.args['layer']['_latlngs']
            elif '_latlng' in e.args['layer']:
                coords = e.args['layer']['_latlng']
            else:
                ui.notify('Не удалось получить координаты объекта', color='negative')
                return
            print('Перед вызовом show_save_dialog')
            show_save_dialog(coords)

        def show_save_dialog(coords):
            print('show_save_dialog вызван!')
            dialog = ui.dialog()
            with dialog, ui.card():
                ui.label('Сохранить новый объект').classes('text-h6 q-mb-md')
                name_input = ui.input(label='Название').classes('w-full q-mb-sm')
                group_input = ui.input(label='Группа').classes('w-full q-mb-sm')
                notes_input = ui.textarea(label='Заметки').classes('w-full q-mb-md')
                def save():
                    if not name_input.value:
                        ui.notify('Введите название', type='warning')
                        return
                    session = Session()
                    try:
                        # 1. Сохраняем сам полигон (Polygon)
                        polygon = Polygon(
                            user_id=ui.page.user_id,
                            coords=json.dumps(coords)
                        )
                        session.add(polygon)
                        session.flush()  # Получаем polygon.id

                        # 2. Проверяем структуру coords
                        if not (isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list)):
                            raise ValueError(f"Некорректная структура координат: {coords}")

                        # 3. Сохраняем точки полигона (PolygonPoint)
                        for point in coords[0]:
                            if not all(k in point for k in ('lat', 'lng')):
                                raise ValueError(f"Некорректная точка: {point}")
                            point_obj = PolygonPoint(
                                user_id=ui.page.user_id,
                                lat=point['lat'],
                                lng=point['lng'],
                                polygon_id=polygon.id
                            )
                            session.add(point_obj)

                        # 4. Создаём запись в таблице Field
                        field = Field(
                            user_id=ui.page.user_id,
                            name=name_input.value,
                            coordinates=json.dumps(coords),
                            group=group_input.value,
                            notes=notes_input.value,
                            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        session.add(field)

                        session.commit()
                        ui.notify('Объект успешно создан', color='positive')
                        dialog.close()
                        ui.open('/fields')
                    except Exception as e:
                        session.rollback()
                        print(f"Ошибка при создании объекта: {e}")
                        ui.notify(f'Ошибка при создании объекта: {e}', color='negative')
                    finally:
                        session.close()
                with ui.row().classes('w-full justify-end'):
                    ui.button('Отмена', on_click=dialog.close).props('flat')
                    ui.button('Сохранить', on_click=save).props('color=positive')
            dialog.open()
        map_view.on('draw:created', handle_field_creation)
    elif action == 'select' and fields:
        field_ids = [int(fid) for fid in fields.split(',') if fid.isdigit()]
        if field_ids:
            # Получаем координаты первого полигона для центрирования
            session = Session()
            field = session.query(Field).filter(Field.id == field_ids[0], Field.user_id == ui.page.user_id).first()
            session.close()
            if field:
                coords = json.loads(field.coordinates)
                # coords[0] — список точек полигона
                if coords and coords[0]:
                    latlngs = coords[0]
                    # Центр полигона (среднее по всем точкам)
                    lat = sum(p['lat'] for p in latlngs) / len(latlngs)
                    lng = sum(p['lng'] for p in latlngs) / len(latlngs)
                    map_view.set_center((lat, lng))
            for field_id in field_ids:
                highlight_polygon(field_id, ui.page.user_id, map_view.id)

    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')


@ui.page('/charts')
def charts_page():
    data_input = ui.textarea(
        label='Enter data for the chart (JSON format)').classes('w-full')
    chart = ui.echart(options={}).classes(
        'w-full h-96')  # Initialize with empty options

    def update_chart():
        try:
            data = json.loads(data_input.value)
            option = {
                'title': {'text': 'Chart'},
                'tooltip': {},
                'xAxis': {'data': data['x']},
                'yAxis': {},
                'series': [{'type': 'bar', 'data': data['y']}],
            }
            chart.options = option
        except json.JSONDecodeError:
            ui.notify('Invalid JSON format', color='negative')

    ui.button('Update Chart', on_click=update_chart).classes('mt-4')


@ui.page('/fields')
def fields_page():
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')
    selected = []

    def on_select(e):
        print('e.selected:', getattr(e, 'selected', None))  # Для отладки
        selected.clear()
        if hasattr(e, 'selected') and e.selected:
            selected.extend(e.selected)
        print('selected:', selected)  # Для отладки

    def delete_selected_fields():
        print('selected:', selected)  # Для отладки
        if not selected:
            ui.notify('Выберите поля для удаления', type='warning')
            return
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Удаление {len(selected)} полей").classes('text-h6 q-mb-md')
            ui.label('Вы уверены, что хотите удалить выбранные поля? Это действие нельзя отменить.').classes('q-mb-md')
            with ui.row().classes('w-full justify-end'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                def confirm_delete():
                    any_deleted = False
                    for field in selected:
                        print('Удаляю:', field)  # Для отладки
                        success, message = delete_field(field['id'], ui.page.user_id)
                        if success:
                            any_deleted = True
                        else:
                            ui.notify(message, type='negative')
                    dialog.close()
                    load_fields()
                    if any_deleted:
                        ui.notify('Поля успешно удалены', color='positive')
                ui.button('Удалить', on_click=confirm_delete).props('color=negative')

    def export_all_fields_to_csv_dialog():
        with ui.dialog() as dialog, ui.card():
            ui.label('Выгрузить все поля в CSV').classes('text-h6 q-mb-md')
            filename_input = ui.input(label='Имя файла', value=f'fields_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv').classes('w-full q-mb-md')
            def export():
                filename = filename_input.value or f'fields_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                path = export_all_fields_to_csv(ui.page.user_id, filename)
                if path:
                    ui.download(path)
                    ui.notify(f'Файл {filename} готов к скачиванию', color='positive')
                else:
                    ui.notify('Ошибка при экспорте', color='negative')
                dialog.close()
            with ui.row().classes('w-full justify-end'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Выгрузить', on_click=export).props('color=primary')

    def edit_field(field_id):
        field = next((f for f in fields_table.rows if f['id'] == field_id), None)
        if not field:
            return
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Редактирование поля: {field['name']}").classes('text-h6 q-mb-md')
            name_input = ui.input(label='Название поля', value=field['name']).classes('w-full q-mb-sm')
            def save():
                if not name_input.value:
                    ui.notify('Введите название поля', type='warning')
                    return
                success, message = update_field(
                    field_id,
                    ui.page.user_id,
                    name=name_input.value
                )
                if success:
                    ui.notify(message, type='positive')
                    dialog.close()
                    load_fields()
                else:
                    ui.notify(message, type='negative')
            with ui.row().classes('w-full justify-end'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Сохранить', on_click=save).props('color=positive')

    def show_field_details(field_id):
        field = next((f for f in fields_table.rows if f['id'] == field_id), None)
        if not field:
            return
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Детали поля: {field['name']}").classes('text-h6 q-mb-md')
            ui.label(f"Создано: {field['created_at']}")
            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('Закрыть', on_click=dialog.close).props('flat')

    def load_fields():
        fields = get_user_fields(ui.page.user_id)
        print('rows for table:', fields)  # Для отладки
        fields_table.rows = fields
        return fields

    def filter_fields():
        fields = get_user_fields(ui.page.user_id)
        if search_text.value:
            fields = [f for f in fields if search_text.value.lower() in f['name'].lower()]
        fields_table.rows = fields

    # --- UI ---
    with ui.card().classes('w-full'):
        ui.label('Управление полями').classes('text-h4 q-mb-md')
        with ui.row().classes('q-mb-md'):
            ui.button('Создать новое поле', on_click=lambda: ui.open('/map?action=create')).props('color=positive')
        search_text = ui.input(label='Поиск по названию').classes('q-mr-md')
        search_text.on('change', filter_fields)
        fields_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                {'name': 'name', 'label': 'Название', 'field': 'name', 'align': 'left'},
                {'name': 'created_at', 'label': 'Создано', 'field': 'created_at', 'align': 'left'}
            ],
            rows=[],
            row_key='id',
            selection='multiple',
            on_select=on_select
        ).classes('w-full')
        # --- Обходной способ удаления по id ---
        with ui.row().classes('q-mt-md'):
            delete_id_input = ui.input(label='ID для удаления').props('type=number').classes('q-mr-md')
            def delete_by_id():
                try:
                    field_id = int(delete_id_input.value)
                except (TypeError, ValueError):
                    ui.notify('Введите корректный ID', color='warning')
                    return
                success, message = delete_field(field_id, ui.page.user_id)
                if success:
                    ui.notify(f'Поле с id={field_id} удалено', color='positive')
                    load_fields()
                else:
                    ui.notify(message, color='negative')
            ui.button('Удалить по id', on_click=delete_by_id).props('color=negative')
        # --- Обходной способ показа полигона по id ---
        with ui.row().classes('q-mt-md'):
            show_id_input = ui.input(label='ID для показа на карте').props('type=number').classes('q-mr-md')
            def show_by_id():
                try:
                    field_id = int(show_id_input.value)
                except (TypeError, ValueError):
                    ui.notify('Введите корректный ID', color='warning')
                    return
                ui.open(f'/map?action=select&fields={field_id}')
            ui.button('Показать полигон на карте по id', on_click=show_by_id).props('color=primary')
            def open_polygon_viewer():
                try:
                    field_id = int(show_id_input.value)
                except (TypeError, ValueError):
                    ui.notify('Введите корректный ID', color='warning')
                    return
                import webbrowser
                webbrowser.open_new_tab(f'http://127.0.0.1:8080/polygon_viewer?id={field_id}')
            ui.button('Открыть в новой вкладке (ограничить область)', on_click=open_polygon_viewer).props('color=secondary')
        with ui.row().classes('q-mt-md'):
            export_id_input = ui.input(label='ID для экспорта параметров').props('type=number').classes('q-mr-md')
            def export_params_by_id():
                try:
                    field_id = int(export_id_input.value)
                except (TypeError, ValueError):
                    ui.notify('Введите корректный ID', color='warning')
                    return
                filename = f'field_{field_id}_params.csv'
                session = Session()
                field = session.query(Field).filter(Field.id == field_id, Field.user_id == ui.page.user_id).first()
                session.close()
                if not field:
                    ui.notify('Поле не найдено', color='negative')
                    return
                # Получаем центр полигона
                coords = json.loads(field.coordinates)
                latlngs = coords[0]
                lat = sum(p['lat'] for p in latlngs) / len(latlngs)
                lng = sum(p['lng'] for p in latlngs) / len(latlngs)
                soil_params = get_arcgis_soil_params(lat, lng)
                save_arcgis_data_to_db(field.id, soil_params)
                fieldnames = [
                    'id', 'name', 'created_at', 'coordinates', 'group', 'notes', 'area', 'soil_type', 'soil_ph', 'humus_content', 'soil_texture', 'elevation', 'slope', 'aspect',
                    'phh2o_0-5cm_mean', 'ocd_0-30cm_mean', 'clay_0-5cm_mean', 'sand_0-5cm_mean', 'silt_0-5cm_mean', 'cec_0-5cm_mean', 'bdod_0-5cm_mean', 'nitrogen_0-5cm_mean'
                ]
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    import csv
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
                    row.update(soil_params)
                    writer.writerow(row)
                ui.download(filename)
                ui.notify(f'Параметры поля {field_id} выгружены в {filename}', color='positive')
            ui.button('Выгрузить параметры по ID (CSV)', on_click=export_params_by_id).props('color=primary')
    load_fields()

def export_field_parameters(field_ids, user_id):
    """Экспорт параметров выбранных полей"""
    try:
        session = Session()
        fields = session.query(Field).filter(
            Field.id.in_(field_ids),
            Field.user_id == user_id
        ).all()
        
        parameters = []
        for field in fields:
            coords = json.loads(field.coordinates)
            field_params = {
                'field_id': field.id,
                'name': field.name,
                'area': field.area,
                'soil': {
                    'type': field.soil_type,
                    'ph': field.soil_ph,
                    'humus': field.humus_content,
                    'texture': field.soil_texture
                },
                'relief': {
                    'elevation': field.elevation,
                    'slope': field.slope,
                    'aspect': field.aspect
                }
            }
            
            # Получаем последний анализ почвы
            soil_analysis = session.query(SoilAnalysis).filter(
                SoilAnalysis.field_id == field.id
            ).order_by(SoilAnalysis.analysis_date.desc()).first()
            
            if soil_analysis:
                field_params['soil_analysis'] = {
                    'date': soil_analysis.analysis_date,
                    'ph': soil_analysis.ph_value,
                    'humus': soil_analysis.humus_percentage,
                    'nitrogen': soil_analysis.nitrogen_content,
                    'phosphorus': soil_analysis.phosphorus_content,
                    'potassium': soil_analysis.potassium_content,
                    'organic_matter': soil_analysis.organic_matter
                }
            
            # Получаем климатические данные
            climate_data = session.query(ClimateData).filter(
                ClimateData.field_id == field.id
            ).order_by(ClimateData.date.desc()).first()
            
            if climate_data:
                field_params['climate'] = {
                    'date': climate_data.date,
                    'temperature': climate_data.temperature,
                    'precipitation': climate_data.precipitation,
                    'humidity': climate_data.humidity,
                    'wind_speed': climate_data.wind_speed,
                    'solar_radiation': climate_data.solar_radiation
                }
            
            parameters.append(field_params)
        
        # Создаем файл с параметрами
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'field_parameters_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(parameters, f, ensure_ascii=False, indent=4)
            
        return filename
    except Exception as e:
        print(f"Ошибка при экспорте параметров полей: {e}")
        return None
    finally:
        session.close()

def get_user_fields(user_id, group=None):
    """Получение списка полей пользователя (только id, name, created_at)"""
    try:
        session = Session()
        query = session.query(Field).filter(Field.user_id == user_id)
        if group:
            query = query.filter(Field.group == group)
        fields = query.all()
        result = []
        for field in fields:
            field_data = {
                'id': field.id,
                'name': field.name,
                'created_at': field.created_at,
            }
            result.append(field_data)
        return result
    except Exception as e:
        print(f"Ошибка при получении списка полей: {e}")
        return []
    finally:
        session.close()

def update_field(field_id, user_id, **kwargs):
    """Обновление параметров поля"""
    try:
        session = Session()
        field = session.query(Field).filter(
            Field.id == field_id,
            Field.user_id == user_id
        ).first()
        
        if not field:
            return False, "Поле не найдено"
            
        # Обновляем только переданные параметры
        for key, value in kwargs.items():
            if hasattr(field, key):
                setattr(field, key, value)
        
        field.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session.commit()
        return True, "Поле успешно обновлено"
    except Exception as e:
        print(f"Ошибка при обновлении поля: {e}")
        session.rollback()
        return False, f"Ошибка при обновлении поля: {str(e)}"
    finally:
        session.close()

def delete_field(field_id, user_id):
    """Удаление поля"""
    try:
        session = Session()
        field = session.query(Field).filter(
            Field.id == field_id,
            Field.user_id == user_id
        ).first()
        
        if not field:
            return False, "Поле не найдено"
            
        # Удаляем связанные данные
        session.query(SoilAnalysis).filter(SoilAnalysis.field_id == field_id).delete()
        session.query(ClimateData).filter(ClimateData.field_id == field_id).delete()
        
        # Удаляем само поле
        session.delete(field)
        session.commit()
        return True, "Поле успешно удалено"
    except Exception as e:
        print(f"Ошибка при удалении поля: {e}")
        session.rollback()
        return False, f"Ошибка при удалении поля: {str(e)}"
    finally:
        session.close()

# --- Функция экспорта всех полей в CSV ---
def export_all_fields_to_csv(user_id, filename):
    try:
        session = Session()
        fields = session.query(Field).filter(Field.user_id == user_id).all()
        session.close()
        if not fields:
            return None
        fieldnames = ['id', 'name', 'created_at', 'coordinates', 'group', 'notes']
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for field in fields:
                writer.writerow({
                    'id': field.id,
                    'name': field.name,
                    'created_at': field.created_at,
                    'coordinates': field.coordinates,
                    'group': field.group,
                    'notes': field.notes
                })
        return filename
    except Exception as e:
        print(f'Ошибка при экспорте в CSV: {e}')
        return None

# Initialize the database
initialize_db()

@ui.page('/polygon_viewer')
def polygon_viewer_page(id: int = None):
    if not id:
        return
    session = Session()
    user = session.query(User).first()
    test_user_id = user.user_id if user else None
    polygon_points = session.query(PolygonPoint).filter(
        PolygonPoint.polygon_id == id,
        PolygonPoint.user_id == test_user_id
    ).all()
    session.close()
    latlngs = [[point.lat, point.lng] for point in polygon_points]
    if not polygon_points:
        ui.label(f'Полигон с id={id} не найден').classes('text-h6 q-mb-md')
        return
    if latlngs and latlngs[0] != latlngs[-1]:
        latlngs.append(latlngs[0])
    # Костыль: вычисляем центр полигона
    center_lat = sum(p[0] for p in latlngs) / len(latlngs)
    center_lng = sum(p[1] for p in latlngs) / len(latlngs)
    map_view = ui.leaflet(center=[center_lat, center_lng], zoom=15).classes('h-96 w-full')
    ui.run_javascript(f"""
        window.mapInstances = window.mapInstances || {{}};
        document.addEventListener('leaflet_map_ready_' + {map_view.id}, function() {{
            try {{
                const map = window.mapInstances['{map_view.id}'];
                if (map) {{
                    const points = {json.dumps(latlngs)};
                    const polygon = L.polygon(points, {{
                        color: 'blue',
                        weight: 4,
                        fillColor: 'yellow',
                        fillOpacity: 0.3
                    }}).addTo(map);
                    map.setView([{center_lat}, {center_lng}], 15);
                    // Отключаем все действия пользователя
                    map.dragging.disable();
                    map.touchZoom.disable();
                    map.doubleClickZoom.disable();
                    map.scrollWheelZoom.disable();
                    map.boxZoom.disable();
                    map.keyboard.disable();
                    if (map.tap) map.tap.disable();
                    map.zoomControl.remove();
                    // Кнопка для скачивания PNG
                    if (!document.getElementById('download_map_btn')) {{
                        var btn = document.createElement('button');
                        btn.innerText = 'Скачать картинку с полигоном';
                        btn.id = 'download_map_btn';
                        btn.style = 'position:absolute;top:10px;right:10px;z-index:1000;padding:8px;background:#1976d2;color:#fff;border:none;border-radius:4px;cursor:pointer;';
                        btn.onclick = function() {{
                            if (window.leafletImage) {{
                                window.leafletImage(map, function(err, canvas) {{
                                    var img = document.createElement('a');
                                    img.download = 'polygon_map.png';
                                    img.href = canvas.toDataURL();
                                    img.click();
                                }});
                            }} else {{
                                alert('leaflet-image.js не подключён');
                            }}
                        }};
                        map.getContainer().appendChild(btn);
                    }}
                }}
            }} catch(e) {{
                console.error('Ошибка при отрисовке полигона:', e);
            }}
        }}, {{ once: true }});
        if (window.mapInstances && window.mapInstances['{map_view.id}']) {{
            try {{
                const map = window.mapInstances['{map_view.id}'];
                const points = {json.dumps(latlngs)};
                const polygon = L.polygon(points, {{
                    color: 'blue',
                    weight: 4,
                    fillColor: 'yellow',
                    fillOpacity: 0.3
                }}).addTo(map);
                map.setView([{center_lat}, {center_lng}], 15);
                map.dragging.disable();
                map.touchZoom.disable();
                map.doubleClickZoom.disable();
                map.scrollWheelZoom.disable();
                map.boxZoom.disable();
                map.keyboard.disable();
                if (map.tap) map.tap.disable();
                map.zoomControl.remove();
                if (!document.getElementById('download_map_btn')) {{
                    var btn = document.createElement('button');
                    btn.innerText = 'Скачать картинку с полигоном';
                    btn.id = 'download_map_btn';
                    btn.style = 'position:absolute;top:10px;right:10px;z-index:1000;padding:8px;background:#1976d2;color:#fff;border:none;border-radius:4px;cursor:pointer;';
                    btn.onclick = function() {{
                        if (window.leafletImage) {{
                            window.leafletImage(map, function(err, canvas) {{
                                var img = document.createElement('a');
                                img.download = 'polygon_map.png';
                                img.href = canvas.toDataURL();
                                img.click();
                            }});
                        }} else {{
                            alert('leaflet-image.js не подключён');
                        }}
                    }};
                    map.getContainer().appendChild(btn);
                }}
            }} catch(e) {{
                console.error('Ошибка при прямой отрисовке полигона:', e);
            }}
        }}
    """)
    ui.button('Назад', on_click=lambda: ui.open('/fields')).classes('mt-4')

def get_arcgis_soil_params(lat, lng):
    """
    Получить почвенные параметры через ArcGIS REST API по координате.
    Пример использует слой Soils (Layer 4) из публичного MapServer.
    """
    endpoint = "https://www.ncmhtd.com/arcgis/rest/services/NRCS/NRCS_SoilData/MapServer/4/query"
    params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json"
    }
    try:
        r = requests.get(endpoint, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("features"):
                attrs = data["features"][0]["attributes"]
                return attrs
            else:
                print("Нет данных по данной точке")
                return {}
        else:
            print("Ошибка ArcGIS REST:", r.status_code, r.text)
            return {}
    except Exception as e:
        print("Ошибка запроса к ArcGIS REST:", e)
        return {}

def save_arcgis_data_to_db(field_id, arcgis_data):
    session = Session()
    try:
        record = FieldArcGISData(
            field_id=field_id,
            data=arcgis_data,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(record)
        session.commit()
    except Exception as e:
        print(f"Ошибка при сохранении ArcGIS данных: {e}")
        session.rollback()
    finally:
        session.close()

ui.run()
