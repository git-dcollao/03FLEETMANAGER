from flask import Blueprint, render_template, redirect, url_for, session, request, send_file, jsonify
from app import IP, PORT
from app.db import db 
from app.models import Usuario, Area, Vehiculo, CoordenadasVehiculo, Parametro
from app.funciones import transformador, coordenada_pertenece_a_areas, obtener_distancia_ruta, calcular_distancia, calcular_pendiente, calcular_tiempo, obtener_datos_informe
import pandas as pd
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import tempfile
import locale

main = Blueprint('main', __name__)

@main.route('/inicio', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        personal_usuario = usuario.personal
        return render_template('index.html', username = username, persona = personal_usuario)
    else:
        return redirect(url_for('auth.login'))

@main.route('/menu_coordenadas', methods=['GET', 'POST'])
def menu_coordenadas():
    if 'username' in session:
        return render_template('menu/menu_coordenadas.html')
    else:
        return redirect(url_for('auth.login'))

@main.route('/menu_area', methods=['GET', 'POST'])
def menu_area():
    if 'username' in session:
        return render_template('menu/menu_area.html')
    else:
        return redirect(url_for('auth.login'))

@main.route('/menu_vehiculo', methods=['GET', 'POST'])
def menu_vehiculo():
    if 'username' in session:
        return render_template('menu/menu_vehiculo.html')
    else:
        return redirect(url_for('auth.login'))

@main.route('/menu_personal', methods=['GET', 'POST'])
def menu_personal():
    if 'username' in session:
        return render_template('menu/menu_personal.html')
    else:
        return redirect(url_for('auth.login'))

@main.route('/menu_equipo', methods=['GET', 'POST'])
def menu_equipo():
    if 'username' in session:
        return render_template('menu/menu_equipo.html')
    else:
        return redirect(url_for('auth.login'))

@main.route('/menu_datos', methods=['GET', 'POST'])
def menu_datos():
    if 'username' in session:
        return render_template('menu/menu_datos.html')
    else:
        return redirect(url_for('auth.login'))

@main.route('/carga_masiva_coordenadas_vehiculo', methods=['GET', 'POST'])
def carga_masiva_coordenadas_vehiculo():
    if 'username' in session:
        if request.method == 'POST':
            archivo_excel = request.files['archivo_excel']

            if archivo_excel and archivo_excel.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(archivo_excel, header=None)

                for i, row in df.iterrows():
                    if 'Longitud' in row.values and 'Latitud' in row.values:
                        df.columns = row
                        df = df[i+1:]
                        break

                if 'Longitud' not in df.columns or 'Latitud' not in df.columns:
                    return "No se encontraron las columnas 'Longitud' y 'Latitud' en el archivo Excel.", 400

                df = df.dropna(subset=['Longitud', 'Latitud'])

                try:
                    coordenadas_vehiculo = []
                    delta_latitud_anterior = 0
                    delta_longitud_anterior = 0
                    pendiente_anterior = 0

                    for index, row in df.iterrows():
                        vehiculo = db.session.query(Vehiculo).filter_by(gps=row['IMEI']).first()
                        areas = Area.query.filter(Area.id_dpto_empresa == vehiculo.id_dpto_empresa).all()

                        fecha_valor = row['Fecha']

                        if isinstance(fecha_valor, datetime):
                            fecha_formateada = fecha_valor.strftime('%Y-%m-%d')
                        else:
                            fecha_str = str(fecha_valor).strip()
                            try:
                                fecha_obj = datetime.strptime(fecha_str, '%d-%m-%Y')
                            except ValueError:
                                return f"Formato de fecha no reconocido: {fecha_str}", 400

                            fecha_formateada = fecha_obj.strftime('%Y-%m-%d')

                        longitud, latitud = row['Longitud'], row['Latitud']
                        utm_longitud, utm_latitud = transformador.transform(longitud, latitud)

                        existing_coordinate = CoordenadasVehiculo.query.filter_by(
                            id_vehiculo=vehiculo.id_vehiculo,
                            fecha=fecha_formateada,
                            hora=row['Hora'],
                            longitud=utm_longitud,
                            latitud=utm_latitud,
                            grados_longitud=longitud,
                            grados_latitud=latitud,
                        ).first()

                        if not existing_coordinate:

                            nueva_coordenada_vehiculo = CoordenadasVehiculo(
                                latitud=utm_latitud,
                                longitud=utm_longitud,
                                grados_latitud=row['Latitud'],
                                grados_longitud=row['Longitud'],
                                fecha=fecha_formateada,
                                hora=row['Hora'],
                                vehiculo=vehiculo,
                                estado=1,
                                distancia_r=0,
                                distancia_m=0,
                            )
                            db.session.add(nueva_coordenada_vehiculo)
                            coordenadas_vehiculo.append(nueva_coordenada_vehiculo)

                    for i in range(len(coordenadas_vehiculo)):
                        coord_curr = coordenadas_vehiculo[i]

                        if i == 0 or (i > 0 and coordenadas_vehiculo[i - 1].fecha != coord_curr.fecha):
                            distancia_r = 0
                            distancia_m = 0
                            delta_latitud_anterior = 0
                            delta_longitud_anterior = 0
                            pendiente_anterior = 0
                        else:
                            coord_prev = coordenadas_vehiculo[i - 1]
                            coord_next = coordenadas_vehiculo[i + 1] if i + 1 < len(coordenadas_vehiculo) else None
                            coord_subnext = coordenadas_vehiculo[i + 2] if i + 2 < len(coordenadas_vehiculo) else None
                            coord_subnext2 = coordenadas_vehiculo[i + 3] if i + 3 < len(coordenadas_vehiculo) else None

                            coord_prev_point = (coord_prev.grados_longitud, coord_prev.grados_latitud)
                            coord_curr_point = (coord_curr.grados_longitud, coord_curr.grados_latitud)

                            url = f"http://{IP}:{PORT}/route/v1/driving/{coord_prev_point[0]},{coord_prev_point[1]};{coord_curr_point[0]},{coord_curr_point[1]}?overview=false"
                            distancia_r = obtener_distancia_ruta(url)
                            distancia_m = calcular_distancia(coord_prev, coord_curr)
                            pendiente, delta_latitud, delta_longitud = calcular_pendiente(coord_prev, coord_curr)
                            distancia_r1 = distancia_r2 = distancia_r3 = 0

                            caso_actual_1 = delta_latitud < 0 and delta_longitud > 0 and pendiente < 0
                            caso_actual_2 = delta_latitud > 0 and delta_longitud < 0 and pendiente < 0
                            caso_actual_3 = delta_latitud > 0 and delta_longitud > 0 and pendiente > 0
                            caso_actual_4 = delta_latitud < 0 and delta_longitud < 0 and pendiente > 0

                            caso_antiguo_1 = delta_latitud_anterior < 0 and delta_longitud_anterior > 0 and pendiente_anterior < 0
                            caso_antiguo_2 = delta_latitud_anterior > 0 and delta_longitud_anterior < 0 and pendiente_anterior < 0
                            caso_antiguo_3 = delta_latitud_anterior > 0 and delta_longitud_anterior > 0 and pendiente_anterior > 0
                            caso_antiguo_4 = delta_latitud_anterior < 0 and delta_longitud_anterior < 0 and pendiente_anterior > 0

                            if (((caso_actual_1 and caso_antiguo_2) or 
                                (caso_actual_2 and caso_antiguo_1) or 
                                (caso_actual_3 and caso_antiguo_4) or 
                                (caso_actual_4 and caso_antiguo_3))):
                                coord_curr.estado = 2
                                db.session.commit()
                                continue

                            delta_latitud_anterior = delta_latitud
                            delta_longitud_anterior = delta_longitud
                            pendiente_anterior = pendiente
                            if coord_next:
                                coord_next_point = (coord_next.grados_longitud, coord_next.grados_latitud)
                                url_r1 = f"http://{IP}:{PORT}/route/v1/driving/{coord_curr_point[0]},{coord_curr_point[1]};{coord_next_point[0]},{coord_next_point[1]}?overview=false"
                                distancia_r1 = obtener_distancia_ruta(url_r1)

                            if coord_subnext:
                                coord_subnext_point = (coord_subnext.grados_longitud, coord_subnext.grados_latitud)
                                url_r2 = f"http://{IP}:{PORT}/route/v1/driving/{coord_curr_point[0]},{coord_curr_point[1]};{coord_subnext_point[0]},{coord_subnext_point[1]}?overview=false"
                                distancia_r2 = obtener_distancia_ruta(url_r2)

                            if coord_subnext2:
                                coord_subnext2_point = (coord_subnext2.grados_longitud, coord_subnext2.grados_latitud)
                                url_r3 = f"http://{IP}:{PORT}/route/v1/driving/{coord_curr_point[0]},{coord_curr_point[1]};{coord_subnext2_point[0]},{coord_subnext2_point[1]}?overview=false"
                                distancia_r3 = obtener_distancia_ruta(url_r3)

                            if distancia_r1 and distancia_r2 and distancia_r3:
                                if distancia_r1 > distancia_r2:
                                    coord_subnext.estado = 2
                                    db.session.commit()
                                if distancia_r2 > distancia_r3:
                                    coord_subnext2.estado = 2
                                    db.session.commit()
                        print(i)
                        coord_curr.distancia_r = distancia_r
                        coord_curr.distancia_m = distancia_m

                        if int(distancia_r) > int(distancia_m):
                            coord_curr.estado = 2
                            db.session.commit()

                    db.session.commit()
                    return redirect(url_for('main.menu_vehiculo'))
                except IntegrityError as e:
                    print(f"Error de integridad: {e}")
                    return 'Error al guardar las coordenadas del vehículo en la base de datos.', 500
                except Exception as e:
                    print(f"Error desconocido: {e}")
                    return 'Error al procesar el archivo Excel.', 500
        else:
            return render_template('cargas/carga_masiva_coord_vehiculo.html')
    else:
        return redirect(url_for('auth.login'))
    
@main.route('/seleccionar_vehiculo', methods=['GET', 'POST'])
def seleccionar_vehiculo():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        
        if request.method == 'POST':
            seleccion = request.form['seleccion']
            id_vehiculo = request.form['id_vehiculo']
            
            if seleccion == 'Informe':
                return redirect(url_for('main.informe_vehiculo', id_vehiculo=id_vehiculo))
            elif seleccion == 'Trayecto':
                return redirect(url_for('main.ver_trayecto', id_vehiculo=id_vehiculo))

        vehiculos = sorted(Vehiculo.query.filter(Vehiculo.id_dpto_empresa==departamento_usuario).all(), key=lambda x: locale.strxfrm(x.patente))

        return render_template('seleccionar_vehiculo.html', vehiculos=vehiculos)
    else:
        return redirect(url_for('auth.login'))

@main.route('/informe_vehiculo/<int:id_vehiculo>', methods=['GET', 'POST'])
def informe_vehiculo(id_vehiculo):
    if 'username' in session:
        fecha_seleccionada = request.form.get('fecha') if request.method == 'POST' else None
        informe_data, vehiculo, fechas_disponibles = obtener_datos_informe(id_vehiculo, fecha_seleccionada)
        if not vehiculo:
            return redirect(url_for('auth.login'))
        return render_template('informe.html', informe_data=informe_data, vehiculo=vehiculo, fecha_seleccionada=fecha_seleccionada, fechas_disponibles=fechas_disponibles)
    else:
        return redirect(url_for('auth.login'))
    
@main.route('/descargar_informe_excel', methods=['POST'])
def descargar_informe_excel():
    if 'username' in session:
        id_vehiculo = request.form['id_vehiculo']

        coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo, estado=1).order_by(CoordenadasVehiculo.fecha, CoordenadasVehiculo.hora).all()
        vehiculo = Vehiculo.query.get(id_vehiculo)

        fecha_anterior = None
        areas = Area.query.filter(Area.id_dpto_empresa == vehiculo.id_dpto_empresa).all()
        parametros = Parametro.query.filter(Parametro.id_dpto_empresa == vehiculo.id_dpto_empresa).all()
        informe_data = []

        for i in range(len(coordenadas_vehiculo)):
            distancia = calcular_distancia(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i]) if i > 0 else 0
            tiempo_transcurrido = calcular_tiempo(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i]) if i > 0 else 0

            tipos_de_area, nombres_de_area = coordenada_pertenece_a_areas(coordenadas_vehiculo[i], areas)

            cuadrantes = next((nombre for tipo, nombre in zip(tipos_de_area, nombres_de_area) if tipo == 'cuadrantes'), "N/A")
            sectores = next((nombre for tipo, nombre in zip(tipos_de_area, nombres_de_area) if tipo == 'sectores'), "N/A")
            z_trabajos = next((nombre for tipo, nombre in zip(tipos_de_area, nombres_de_area) if tipo == 'z_trabajos'), "N/A")
            cercos = next((nombre for tipo, nombre in zip(tipos_de_area, nombres_de_area) if tipo == 'cercos'), "N/A")

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
                        velocidad_kilometros = 0
                        distancia = 0
                        estado = 'Detenido en un cerco'
                        break
                    else:
                        estado = 'Activo'
            else:
                estado = 'No existe parametro'

            informe_data.append({
                'Patente': vehiculo.patente,
                'Fecha': coordenadas_vehiculo[i].fecha,
                'Hora': coordenadas_vehiculo[i].hora,
                'Latitud': coordenadas_vehiculo[i].latitud,
                'Longitud': coordenadas_vehiculo[i].longitud,
                'Distancia (m)': distancia,
                'Velocidad (Km/h)': round(velocidad_kilometros),
                'Tiempo (s)': round(tiempo_transcurrido),
                'Estado': estado,
                'Cuadrantes': cuadrantes,
                'Sectores': sectores,
                'Z_Trabajos': z_trabajos,
                'Cercos': cercos
            })

            fecha_anterior = coordenadas_vehiculo[i].fecha

        df = pd.DataFrame(informe_data)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            excel_filename = tmp.name

        df.to_excel(excel_filename, index=False)

        return send_file(excel_filename, as_attachment=True, download_name=f'informe_vehiculo_{vehiculo.patente}.xlsx')

    else:
        return redirect(url_for('auth.login'))
    
@main.route('/ver_trayecto/<int:id_vehiculo>')
def ver_trayecto(id_vehiculo):
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa

        vehiculo = Vehiculo.query.get(id_vehiculo)
        coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo, estado=1).order_by(CoordenadasVehiculo.fecha.desc(), CoordenadasVehiculo.hora).all()
        
        coordenadas_json = []
        fechas_con_coordenadas = set()
        fecha_anterior = None

        for i, coord in enumerate(coordenadas_vehiculo):
            j = i + 1
            while j < len(coordenadas_vehiculo):
                coord_siguiente_valida = coordenadas_vehiculo[j]

                distancia = calcular_distancia(coord, coord_siguiente_valida)
                tiempo_transcurrido = calcular_tiempo(coord, coord_siguiente_valida)

                if not distancia:
                    break

                velocidad = 0 if tiempo_transcurrido == 0 else distancia / tiempo_transcurrido
                velocidad_kilometros = velocidad * 3.6

                if fecha_anterior != coordenadas_vehiculo[j].fecha:
                    coordenadas_json.append({
                        'latitud': coordenadas_vehiculo[j].grados_latitud,
                        'longitud': coordenadas_vehiculo[j].grados_longitud,
                        'fecha': coordenadas_vehiculo[j].fecha.strftime('%Y-%m-%d'),
                        'hora': coordenadas_vehiculo[j].hora.strftime('%H:%M:%S'),
                        'velocidad': round(velocidad_kilometros) if velocidad_kilometros is not None else None,
                        'distancia': 0,
                        'estado': coordenadas_vehiculo[j].estado
                    })
                else:
                    coordenadas_json.append({
                        'latitud': coordenadas_vehiculo[j].grados_latitud,
                        'longitud': coordenadas_vehiculo[j].grados_longitud,
                        'fecha': coordenadas_vehiculo[j].fecha.strftime('%Y-%m-%d'),
                        'hora': coordenadas_vehiculo[j].hora.strftime('%H:%M:%S'),
                        'velocidad': round(velocidad_kilometros) if velocidad_kilometros is not None else None,
                        'distancia': round(distancia) if distancia is not None else None,
                        'estado': coordenadas_vehiculo[j].estado
                    })

                fechas_con_coordenadas.add(coordenadas_vehiculo[j].fecha.strftime('%Y-%m-%d'))
                fecha_anterior = coordenadas_vehiculo[j].fecha
                break

        fechas_disponibles = list(reversed(sorted(fechas_con_coordenadas)))

        areas = Area.query.filter(Area.id_dpto_empresa == departamento_usuario).all()
        areas_json = []

        for area in areas:
            area_coords = []
            for coord in area.coordenadas:
                area_coords.append({
                    'latitud': coord.grados_latitud,
                    'longitud': coord.grados_longitud,
                    'nombre_area': area.nombre_area,
                    'tipo_area': area.tipo_area
                })
            areas_json.append({
                'nombre_area': area.nombre_area,
                'tipo_area': area.tipo_area,
                'coordenadas': area_coords
            })

        return render_template('ver_trayecto.html', vehiculo=vehiculo, coordenadas_vehiculo=coordenadas_json, fechas_disponibles=fechas_disponibles, areas=areas_json)
    else:
        return redirect(url_for('auth.login'))
    
@main.route('/carga_masiva_vehiculo', methods=['GET', 'POST'])
def carga_masiva_vehiculo():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        if request.method == 'POST':
            archivo_excel = request.files['archivo_excel']

            if archivo_excel and archivo_excel.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(archivo_excel, header=None)

                for i, row in df.iterrows():
                    if 'IMEI' in row.values:
                        df.columns = row
                        df = df[i+1:]
                        break

                if 'IMEI' not in df.columns:
                    return "No se encontró la columna 'IMEI' en el archivo Excel.", 400

                df = df.dropna(subset=['IMEI'])

                try:
                    for index, row in df.iterrows():
                        vehiculo_existente = db.session.query(Vehiculo).filter_by(gps=row['IMEI']).first()

                        if vehiculo_existente:
                            vehiculo_existente.patente = row['Vehiculo']
                            nuevo_vehiculo = vehiculo_existente
                        else:
                            nuevo_vehiculo = Vehiculo(
                                patente=row['Vehiculo'],
                                gps=row['IMEI'],
                                id_dpto_empresa=departamento_usuario,
                                restriccion=1
                            )
                            db.session.add(nuevo_vehiculo)

                    db.session.commit()

                    return redirect(url_for('main.menu_vehiculo'))
                except IntegrityError as e:
                    print(f"Error de integridad: {e}")
                    db.session.rollback()
                except Exception as e:
                    print(f"Error al intentar realizar la commit: {e}")
                    db.session.rollback()
                finally:
                    db.session.close()

        return render_template('cargas/carga_masiva_vehiculo.html')
    else:
        return redirect(url_for('auth.login'))