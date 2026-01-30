from app.models import Area, CoordenadasVehiculo, Coordenadas, Vehiculo, Parametro
from flask import session
from app import create_app
from app.db import db 
from math import radians, sin, cos, sqrt, atan2
from shapely.geometry import Point, Polygon
from pyproj import Transformer, CRS
from datetime import datetime
import pandas as pd
import requests
import json

crs_actual = CRS.from_epsg(4326)
crs_nuevo = CRS.from_epsg(32719)
transformador = Transformer.from_crs(crs_actual, crs_nuevo, always_xy=True)

def guardar_areas_trabajo(tipo_area, areas_trabajo):
    app = create_app()

    with app.app_context():
        for numero, area in areas_trabajo.items():
            nueva_area = Area(nombre_area=area['nombre'],
                                tipo_area=tipo_area)
            db.session.add(nueva_area)

        try:
            db.session.commit()
        except Exception as e:
            print(f"Error al intentar realizar la commit: {e}")
            db.session.rollback()

def ingresar_area_trabajo(tipo_area, areas_trabajo, nombre_area, coordenadas, id_area, id_dpto_empresa):
    app = create_app()

    coordenadas_numeros = [[float(coord[0]), float(coord[1])] for coord in json.loads(coordenadas)]
    coordenadas_utm = [transformador.transform(coord[1], coord[0]) for coord in coordenadas_numeros]
    with app.app_context():
        nueva_area = Area(nombre_area=str(nombre_area),
                            tipo_area=tipo_area, 
                            id_dpto_empresa=id_dpto_empresa)
        db.session.add(nueva_area)

        try:
            db.session.commit()
        except Exception as e:
            print(f"Error al intentar realizar la commit: {e}")
            db.session.rollback()

        id_area = nueva_area.id_area

        for coord_orig, coord_utm in zip(coordenadas_numeros, coordenadas_utm):
            nueva_coordenada = Coordenadas(
                grados_latitud=coord_orig[0],
                grados_longitud=coord_orig[1],
                latitud=json.dumps(coord_utm[1]),
                longitud=json.dumps(coord_utm[0]),
                id_area=id_area
            )
            db.session.add(nueva_coordenada)

        try:
            db.session.commit()
        except Exception as e:
            print(f"Error al intentar realizar la commit: {e}")
            db.session.rollback()

        print(f"{tipo_area.capitalize()} '{nombre_area}' guardado con éxito.")

def obtener_datos_informe(id_vehiculo, fecha_seleccionada=None):

    vehiculo = Vehiculo.query.get(id_vehiculo)
    if not vehiculo:
        return None, None, None

    if fecha_seleccionada == 'mostrarTodo':
        coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo, estado=1).order_by(CoordenadasVehiculo.fecha, CoordenadasVehiculo.hora).all()
    else:
        fecha_seleccionada = fecha_seleccionada or datetime.now().date()
        coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo, fecha=fecha_seleccionada, estado=1).order_by(CoordenadasVehiculo.hora).all()

    informe_data = []
    fechas_disponibles = reversed(sorted(set(coord.fecha.strftime('%Y-%m-%d') for coord in CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo, estado=1).all())))
    fecha_anterior = None
    tiempo_anterior = None
    areas = Area.query.filter(Area.id_dpto_empresa == vehiculo.id_dpto_empresa).all()
    parametros = Parametro.query.filter(Parametro.id_dpto_empresa == vehiculo.id_dpto_empresa).all()

    for i in range(len(coordenadas_vehiculo)):
        distancia = calcular_distancia(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i]) if i > 0 else 0
        tiempo_transcurrido = calcular_tiempo(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i]) if i > 0 else 0
        tipos_de_area, nombres_de_area = coordenada_pertenece_a_areas(coordenadas_vehiculo[i], areas)

        velocidad = 0 if tiempo_transcurrido == 0 else distancia / tiempo_transcurrido
        velocidad_kilometros = velocidad * 3.6

        if not distancia:
            continue

        if parametros:
            parametros_ordenados = sorted(parametros, key=lambda x: x.segundos_parametro, reverse=True)
            for parametro in parametros_ordenados:
                if coordenadas_vehiculo[i].fecha != fecha_anterior:
                    estado = 'Inicio'
                    break
                elif vehiculo.restriccion == 2 and velocidad_kilometros < 1 and distancia > parametro.distancia_parametro:
                    velocidad_kilometros = 0
                    distancia = 0
                    estado = parametro.nombre_parametro
                    break
                elif tiempo_transcurrido > parametro.segundos_parametro and distancia > parametro.distancia_parametro and velocidad < parametro.velocidad_parametro:
                    estado = parametro.nombre_parametro
                    break
                elif 'cercos' in tipos_de_area:
                    estado = 'Detenido en un cerco'
                    velocidad_kilometros = 0
                    distancia = 0
                    break
                else:
                    estado = 'Activo'
        else:
            estado = 'No existe parametro'

        informe_data.append({
            'fecha': coordenadas_vehiculo[i].fecha.strftime('%Y-%m-%d'),
            'hora': coordenadas_vehiculo[i].hora.strftime('%H:%M:%S'),
            'latitud': coordenadas_vehiculo[i].latitud,
            'longitud': coordenadas_vehiculo[i].longitud,
            'distancia': round(distancia),
            'velocidad': round(velocidad_kilometros),
            'tiempo': tiempo_transcurrido,
            'estado': estado,
            'tipos_area': tipos_de_area,
            'nombres_area': nombres_de_area
        })

        fecha_anterior = coordenadas_vehiculo[i].fecha
        tiempo_anterior = datetime.strptime(f"{coordenadas_vehiculo[i].fecha} {coordenadas_vehiculo[i].hora}", "%Y-%m-%d %H:%M:%S")

    return informe_data, vehiculo, fechas_disponibles

def calcular_pendiente(coord_anterior, coord_actual):
    latitud_anterior = float(coord_anterior.latitud)
    longitud_anterior = float(coord_anterior.longitud)
    latitud_actual = float(coord_actual.latitud)
    longitud_actual = float(coord_actual.longitud)

    delta_latitud = latitud_actual - latitud_anterior
    delta_longitud = longitud_actual - longitud_anterior

    if delta_longitud == 0:
        pendiente = 0
    else:
        pendiente = delta_latitud / delta_longitud

    return pendiente, delta_longitud, delta_latitud

def calcular_distancia(coord_1, coord_2):
    R = 6371000

    latitud_1 = radians(float(coord_1.grados_latitud))
    longitud_1 = radians(float(coord_1.grados_longitud))
    latitud_2 = radians(float(coord_2.grados_latitud))
    longitud_2 = radians(float(coord_2.grados_longitud))

    dlon = longitud_2 - longitud_1
    dlat = latitud_2 - latitud_1

    a = sin(dlat / 2)**2 + cos(latitud_1) * cos(latitud_2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distancia = (R * c)
    return distancia

def calcular_tiempo(coord_1, coord_2):
    fecha_hora_actual = datetime.strptime(f"{coord_2.fecha} {coord_2.hora}", "%Y-%m-%d %H:%M:%S")
    fecha_hora_anterior = datetime.strptime(f"{coord_1.fecha} {coord_1.hora}", "%Y-%m-%d %H:%M:%S")
    tiempo_transcurrido = (fecha_hora_actual - fecha_hora_anterior).total_seconds()

    return tiempo_transcurrido

def coordenada_pertenece_a_areas(coordenada, areas):
    if isinstance(coordenada, pd.Series):
        punto = Point(float(coordenada['Latitud']), float(coordenada['Longitud']))
    else:
        punto = Point(float(coordenada.latitud), float(coordenada.longitud))

    tipos_de_area = []
    nombres_de_area = []

    for area in areas:
        coordenadas_area = [(float(coord.latitud), float(coord.longitud)) for coord in area.coordenadas]
        poligono_area = Polygon(coordenadas_area)

        if punto.within(poligono_area):
            tipos_de_area.append(area.tipo_area)
            nombres_de_area.append(area.nombre_area)

    return (tipos_de_area, nombres_de_area) if tipos_de_area else ([], [])

def obtener_distancia_ruta(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 'Ok' and 'routes' in data and len(data['routes']) > 0:
                distance = data['routes'][0].get('distance', 0)
                print(f"✅ OSRM distancia obtenida: {distance} metros")
                return distance
            else:
                print(f"⚠️ OSRM código: {data.get('code', 'unknown')}")
                return 0
        else:
            print(f"❌ OSRM error HTTP {response.status_code}")
            return 0
    except requests.exceptions.Timeout:
        print("❌ OSRM timeout - servidor no responde")
        return 0
    except requests.exceptions.ConnectionError:
        print("❌ OSRM error de conexión - servidor no disponible")
        return 0
    except Exception as e:
        print(f"❌ OSRM error inesperado: {str(e)}")
        return 0