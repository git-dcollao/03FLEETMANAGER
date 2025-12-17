from flask import Blueprint
from app.db import db 
from app.models import Usuario, Vehiculo, CoordenadasVehiculo, Area
from app.funciones import calcular_distancia, calcular_pendiente, transformador, coordenada_pertenece_a_areas
from datetime import datetime, timedelta
import requests

api = Blueprint('api', __name__)

def obtener_vehiculos_linksur(app):
    with app.app_context():
        token = "e0a9528e7a5f181568f797e7f2d7c355"
        url = f"https://smartgps.gpsserver.xyz/v3/apis/global_api/v3.0.0/public/index.php/obtener_posicion_actual/{token}"

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list):
                for vehiculo_data in data:
                    imei = vehiculo_data.get("imei")
                    patente = vehiculo_data.get("plate")

                    vehiculo_existente = Vehiculo.query.filter_by(patente=patente).first()

                    if vehiculo_existente:
                        vehiculo_existente.gps = imei
                        db.session.commit()
                    else:
                        nuevo_vehiculo = Vehiculo(
                            patente=patente,
                            gps=imei,
                            restriccion = 1,
                            id_dpto_empresa = 7,
                        )
                        db.session.add(nuevo_vehiculo)

                db.session.commit()
                print("Vehículos guardados/actualizados correctamente")
            else:
                print("Formato de respuesta inesperado")
        else:
            print("Error al obtener los vehículos")

def obtener_coordenadas_linksur(app):
    with app.app_context():
        vehiculos = Vehiculo.query.filter_by(id_dpto_empresa=7).all()

        if not vehiculos:
            print("No hay vehículos con id_dpto_empresa = 7")
            return

        token = "e0a9528e7a5f181568f797e7f2d7c355"
        url = f"https://smartgps.gpsserver.xyz/v3/apis/global_api/v3.0.0/public/index.php/obtener_posicion_actual/{token}"

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list):
                coordenada_anterior = None
                delta_latitud_anterior = None
                delta_longitud_anterior = None
                pendiente_anterior = None

                for item in data:
                    imei = item.get('imei')
                    latitud = item.get('latitude')
                    longitud = item.get('longitude')
                    fecha = item.get('date')
                    hora = item.get('hour')

                    if not all([imei, latitud, longitud]):
                        print(f"Datos inválidos o incompletos para el vehículo con IMEI {imei}. Se omite.")
                        continue

                    vehiculo = Vehiculo.query.filter_by(gps=imei).first()

                    if not vehiculo:
                        print(f"No se encontró un vehículo con IMEI {imei}.")
                        continue

                    try:
                        utm_longitud, utm_latitud = transformador.transform(longitud, latitud)
                    except Exception as e:
                        print(f"Error en la transformación de coordenadas para IMEI {imei}: {e}")
                        continue

                    coordenada_existente = CoordenadasVehiculo.query.filter_by(
                        latitud=utm_latitud,
                        longitud=utm_longitud,
                        id_vehiculo=vehiculo.id_vehiculo
                    ).first()

                    if not coordenada_existente:
                        nueva_coordenada = CoordenadasVehiculo(
                            latitud=utm_latitud,
                            longitud=utm_longitud,
                            grados_latitud=latitud,
                            grados_longitud=longitud,
                            estado=1,
                            distancia_m=0,
                            distancia_r=None,
                            fecha=datetime.strptime(fecha, '%Y-%m-%d'),
                            hora=datetime.strptime(hora, '%H:%M:%S'),
                            id_vehiculo=vehiculo.id_vehiculo
                        )

                        coordenada_anterior = CoordenadasVehiculo.query.filter_by(
                            id_vehiculo=vehiculo.id_vehiculo
                        ).order_by(CoordenadasVehiculo.fecha.desc(), CoordenadasVehiculo.hora.desc()).first()

                        if coordenada_anterior:
                            pendiente, delta_latitud, delta_longitud = calcular_pendiente(coordenada_anterior, nueva_coordenada)
                            distancia = calcular_distancia(coordenada_anterior, nueva_coordenada)

                            nueva_coordenada.distancia_m = distancia

                            caso_actual_1 = delta_latitud < 0 and delta_longitud > 0 and pendiente < 0
                            caso_actual_2 = delta_latitud > 0 and delta_longitud < 0 and pendiente < 0
                            caso_actual_3 = delta_latitud > 0 and delta_longitud > 0 and pendiente > 0
                            caso_actual_4 = delta_latitud < 0 and delta_longitud < 0 and pendiente > 0

                            if pendiente_anterior is not None and delta_latitud_anterior is not None and delta_longitud_anterior is not None:
                                caso_antiguo_1 = delta_latitud_anterior < 0 and delta_longitud_anterior > 0 and pendiente_anterior < 0
                                caso_antiguo_2 = delta_latitud_anterior > 0 and delta_longitud_anterior < 0 and pendiente_anterior < 0
                                caso_antiguo_3 = delta_latitud_anterior > 0 and delta_longitud_anterior > 0 and pendiente_anterior > 0
                                caso_antiguo_4 = delta_latitud_anterior < 0 and delta_longitud_anterior < 0 and pendiente_anterior > 0

                                if ((caso_actual_1 and caso_antiguo_2) or 
                                    (caso_actual_2 and caso_antiguo_1) or 
                                    (caso_actual_3 and caso_antiguo_4) or 
                                    (caso_actual_4 and caso_antiguo_3)):
                                    nueva_coordenada.estado = 2

                            pendiente_anterior = pendiente
                            delta_latitud_anterior = delta_latitud
                            delta_longitud_anterior = delta_longitud

                        areas = Area.query.filter_by(id_dpto_empresa=7).all()

                        # Determinar a qué área pertenece la coordenada
                        tipos_de_area, nombres_de_area = coordenada_pertenece_a_areas(nueva_coordenada, areas)

                        # Asignar el tipo de área
                        if tipos_de_area:
                            nueva_coordenada.tipo_area = tipos_de_area[0]

                        db.session.add(nueva_coordenada)
                        db.session.commit()

            print("Coordenadas LINKSUR actualizadas exitosamente.")
        else:
            print("Error al obtener coordenadas")

def obtener_vehiculos_cosemar(app):
    with app.app_context():
        url = "https://api.inducomgps.com/v1/vehiculos?fields[]=patente"
        headers = {
            "Authorization-api-key": "71c627fc-8987-46b9-93f8-4d257a2a26fc"
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            for vehiculo_data in data.get('data', []):
                vehiculo_existente = Vehiculo.query.filter_by(patente=vehiculo_data['patente']).first()
                
                if not vehiculo_existente:
                    vehiculo = Vehiculo(
                        patente=vehiculo_data['patente'],
                        id_gps=vehiculo_data['vehiculo_id'],
                        gps=None,
                        estado=None,
                        restriccion = 1,
                        id_dpto_empresa=7,
                    )
                    db.session.add(vehiculo)
            db.session.commit()
            print("Vehículos actualizados con éxito")

def obtener_coordenadas_cosemar(app):
    with app.app_context():
        usuarios_staff = Usuario.query.filter_by(staff=4).all()
        for usuario in usuarios_staff:
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa

            vehiculos = Vehiculo.query.filter(Vehiculo.id_dpto_empresa == 7).all()
            
            fin = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            
            for vehiculo in vehiculos:

                id_vehiculo = vehiculo.id_vehiculo
                id_gps = vehiculo.id_gps

                if id_gps:

                    ultima_coordenada = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo).order_by(CoordenadasVehiculo.fecha.desc(), CoordenadasVehiculo.hora.desc()).first()

                    if ultima_coordenada:
                        inicio = datetime.combine(ultima_coordenada.fecha, ultima_coordenada.hora).strftime('%Y-%m-%dT%H:%M:%SZ')
                    else:
                        inicio = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

                    url = f"https://api.inducomgps.com/v1/vehiculos/{id_gps}/posiciones?start={inicio}&end={fin}"
                    headers = {
                        "Authorization-api-key": "71c627fc-8987-46b9-93f8-4d257a2a26fc"
                    }

                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()

                        coordenada_anterior = None
                        delta_latitud_anterior = None
                        delta_longitud_anterior = None
                        pendiente_anterior = None

                        for posicion in data.get('data', []):
                            fecha_hora = datetime.strptime(posicion['ts_posicion'], '%Y-%m-%d %H:%M:%S')
                            utm_longitud, utm_latitud = transformador.transform(posicion['longitud'], posicion['latitud'])

                            coordenada_existente = CoordenadasVehiculo.query.filter_by(
                                id_vehiculo=id_vehiculo,
                                fecha=fecha_hora.date(),
                                hora=fecha_hora.time(),
                                longitud=utm_longitud,
                                latitud=utm_latitud
                            ).first()

                            if coordenada_existente:
                                continue

                            distancia = 0

                            if coordenada_anterior:
                                distancia = calcular_distancia(coordenada_anterior, CoordenadasVehiculo(
                                    latitud=utm_latitud,
                                    longitud=utm_longitud,
                                    grados_latitud=posicion['latitud'],
                                    grados_longitud=posicion['longitud'],
                                    fecha=fecha_hora.date(),
                                    hora=fecha_hora.time(),
                                    estado=1,
                                    distancia_r=None,
                                    distancia_m=0,
                                    id_vehiculo=id_vehiculo
                                ))

                            # Determinar el tipo de área donde se encuentra la coordenada
                            areas = Area.query.filter_by(id_dpto_empresa=7)
                            tipos_de_area, _ = coordenada_pertenece_a_areas(CoordenadasVehiculo(
                                latitud=utm_latitud,
                                longitud=utm_longitud,
                                grados_latitud=posicion['latitud'],
                                grados_longitud=posicion['longitud'],
                                fecha=fecha_hora.date(),
                                hora=fecha_hora.time(),
                                estado=1,
                                distancia_r=None,
                                distancia_m=distancia,
                                id_vehiculo=id_vehiculo
                            ), areas)

                            tipo_area = tipos_de_area[0] if tipos_de_area else None  # Guardar el primer tipo de área encontrado

                            coordenada = CoordenadasVehiculo(
                                latitud=utm_latitud,
                                longitud=utm_longitud,
                                grados_latitud=posicion['latitud'],
                                grados_longitud=posicion['longitud'],
                                fecha=fecha_hora.date(),
                                hora=fecha_hora.time(),
                                estado=1,
                                distancia_r=None,
                                distancia_m=distancia,
                                id_vehiculo=id_vehiculo,
                                tipo_area=tipo_area  # Guardar el tipo de área en la base de datos
                            )
                            db.session.add(coordenada)

                            coordenada_anterior = coordenada

                            if coordenada_anterior:
                                pendiente, delta_latitud, delta_longitud = calcular_pendiente(coordenada_anterior, coordenada)

                                caso_actual_1 = delta_latitud < 0 and delta_longitud > 0 and pendiente < 0
                                caso_actual_2 = delta_latitud > 0 and delta_longitud < 0 and pendiente < 0
                                caso_actual_3 = delta_latitud > 0 and delta_longitud > 0 and pendiente > 0
                                caso_actual_4 = delta_latitud < 0 and delta_longitud < 0 and pendiente > 0

                                if (delta_latitud_anterior is not None and delta_longitud_anterior is not None and pendiente_anterior is not None):
                                    caso_antiguo_1 = delta_latitud_anterior < 0 and delta_longitud_anterior > 0 and pendiente_anterior < 0
                                    caso_antiguo_2 = delta_latitud_anterior > 0 and delta_longitud_anterior < 0 and pendiente_anterior < 0
                                    caso_antiguo_3 = delta_latitud_anterior > 0 and delta_longitud_anterior > 0 and pendiente_anterior > 0
                                    caso_antiguo_4 = delta_latitud_anterior < 0 and delta_longitud_anterior < 0 and pendiente_anterior > 0

                                    if (((caso_actual_1 and caso_antiguo_2) or 
                                        (caso_actual_2 and caso_antiguo_1) or 
                                        (caso_actual_3 and caso_antiguo_4) or 
                                        (caso_actual_4 and caso_antiguo_3))):
                                        coordenada.estado = 2
                                        db.session.commit()
                                        continue

                                delta_latitud_anterior = delta_latitud
                                delta_longitud_anterior = delta_longitud
                                pendiente_anterior = pendiente

                        db.session.commit()

                    print(f"Coordenadas actualizadas con éxito para el vehículo con ID: {id_vehiculo}")