from flask import render_template, request, redirect, url_for, send_file, jsonify, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from pyproj import Proj, transform
from sqlalchemy.exc import IntegrityError
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_
import pandas as pd
import tempfile
import hashlib
import base64
import json
import os
from app.funciones import *
from app.models import *
from app.__init__ import IP, PORT

crs_actual = CRS.from_epsg(4326)
crs_nuevo = CRS.from_epsg(32719)
transformador = Transformer.from_crs(crs_actual, crs_nuevo, always_xy=True)

def init_routes(app):
    # INDEX
    @app.route('/inicio', methods=['GET', 'POST'])
    def index():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            personal_usuario = usuario.personal
            return render_template('index.html', username = username, persona = personal_usuario)
        else:
            return redirect(url_for('login'))
        
    # API GPS
    @app.route('/obtener-vehiculos', methods=['GET'])
    def obtener_vehiculos():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            url = "https://api.inducomgps.com/v1/vehiculos?fields[]=patente"
            headers = {
                "Authorization-api-key": "71c627fc-8987-46b9-93f8-4d257a2a26fc"
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                for vehiculo_data in data.get('data', []):
                    # Verifica si el vehículo ya existe en la base de datos
                    vehiculo_existente = Vehiculo.query.filter_by(patente=vehiculo_data['patente']).first()
                    
                    if not vehiculo_existente:
                        # Si el vehículo no existe, lo agrega a la base de datos
                        vehiculo = Vehiculo(
                            patente=vehiculo_data['patente'],
                            id_gps=vehiculo_data['vehiculo_id'],  # Placeholder
                            gps='',  # Placeholder
                            estado='',  # Placeholder
                            id_dpto_empresa=departamento_usuario,
                        )
                        db.session.add(vehiculo)
                db.session.commit()

                return jsonify(data), 200
            else:
                return jsonify({"error": "Error en la solicitud"}), response.status_code
        else:
            return redirect(url_for('login'))
        
    @app.route('/ver-trayecto-vehiculo/', methods=['GET'])
    def ver_trayecto_vehiculo():
        # Obtener la lista de vehículos almacenados
        vehiculos = Vehiculo.query.all()
        
        # Tiempo de fin (fecha y hora actuales)
        fin = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        for vehiculo in vehiculos:
            id_vehiculo = vehiculo.id_vehiculo
            id_gps = vehiculo.id_gps
            
            # Obtener la última fecha y hora de registro de coordenadas para este vehículo
            ultima_coordenada = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo).order_by(CoordenadasVehiculo.fecha.desc(), CoordenadasVehiculo.hora.desc()).first()
            
            if ultima_coordenada:
                inicio = datetime.combine(ultima_coordenada.fecha, ultima_coordenada.hora).strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                inicio = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Construir la URL de la API
            url = "https://api.inducomgps.com/v1/vehiculos/{}/posiciones?start={}&end={}".format(id_gps, inicio, fin)
            headers = {
                "Authorization-api-key": "71c627fc-8987-46b9-93f8-4d257a2a26fc"
            }
            
            # Hacer la solicitud GET a la API
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                coordenada_anterior = None
                delta_latitud_anterior = None
                delta_longitud_anterior = None
                pendiente_anterior = None
                
                for posicion in data.get('data', []):
                    # Extraer la fecha y hora de la posición
                    fecha_hora = datetime.strptime(posicion['ts_posicion'], '%Y-%m-%d %H:%M:%S')
                    utm_longitud, utm_latitud = transformador.transform(posicion['longitud'], posicion['latitud'])
                    
                    # Verificar si la coordenada ya existe en la base de datos
                    coordenada_existente = CoordenadasVehiculo.query.filter_by(
                        id_vehiculo=id_vehiculo,
                        fecha=fecha_hora.date(),
                        hora=fecha_hora.time(),
                        longitud=utm_longitud,
                        latitud=utm_latitud
                    ).first()
                    
                    if not coordenada_existente:
                        distancia = 0  # Inicializa la distancia como 0
                        
                        # Si hay una coordenada anterior, calcular la distancia
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
                        
                        # Guardar la coordenada en la base de datos si no existe
                        coordenada = CoordenadasVehiculo(
                            latitud=utm_latitud,
                            longitud=utm_longitud,
                            grados_latitud=posicion['latitud'],
                            grados_longitud=posicion['longitud'],
                            fecha=fecha_hora.date(),
                            hora=fecha_hora.time(),
                            estado=1,
                            distancia_r=None,  # Puedes ajustar cómo calcular esta distancia
                            distancia_m=distancia,  # Distancia calculada
                            id_vehiculo=id_vehiculo
                        )
                        db.session.add(coordenada)
                        
                        # Actualizar la coordenada anterior
                        coordenada_anterior = coordenada
                        
                    if coordenada_anterior and coordenada:
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

                        # Actualizar las variables para la próxima iteración
                        delta_latitud_anterior = delta_latitud
                        delta_longitud_anterior = delta_longitud
                        pendiente_anterior = pendiente
                
                db.session.commit()

        return jsonify({"message": "Trayectos actualizados"}), 200

    # FUNCIONES CARGO
    @app.route('/crear_cargo', methods=['GET', 'POST'])
    def crear_cargo():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                nombre_cargo = request.form['nombre_cargo']
                nuevo_cargo = Cargo(nombre_cargo=nombre_cargo, 
                                    id_dpto_empresa=departamento_usuario)

                db.session.add(nuevo_cargo)
                db.session.commit()

                return redirect(url_for('crear_cargo'))
            return render_template('datos/crear_cargo.html', username=username)
        else:
            return redirect(url_for('login'))

    # FUNCIONES ROL
    @app.route('/crear_rol', methods=['GET', 'POST'])
    def crear_rol():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()

            if request.method == 'POST':
                departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
                nombre_rol = request.form['nombre_rol']
                nuevo_rol = Rol(nombre_rol=nombre_rol, 
                                id_dpto_empresa=departamento_usuario)

                db.session.add(nuevo_rol)
                db.session.commit()

                return redirect(url_for('crear_rol'))

            return render_template('datos/crear_rol.html', username=username)
        else:
            return redirect(url_for('login'))

    # FUNCIONES TURNO
    @app.route('/crear_turno', methods=['GET', 'POST'])
    def crear_turno():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                nombre_turno = request.form['nombre_turno']
                horario_inicio = request.form['horario_inicio']
                horario_termino = request.form['horario_termino']
                nuevo_turno = Turno(
                    nombre_turno=nombre_turno,
                    horario_inicio=horario_inicio,
                    horario_termino=horario_termino,
                    id_dpto_empresa=departamento_usuario)

                db.session.add(nuevo_turno)
                db.session.commit()

                return redirect(url_for('crear_turno'))

            return render_template('datos/crear_turno.html', username=session['username'])
        else:
            return redirect(url_for('login'))

    # FUNCIONES PROGRAMACION
    @app.route('/crear_programacion', methods=['GET', 'POST'])
    def crear_programacion():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                fecha_hora_str = request.form['fecha_programacion']
                id_personal = request.form['nombre_personal']
                id_area = request.form['nombre_area']
                id_turno = request.form['turno']
                id_vehiculo = request.form['vehiculo']
                id_equipo = request.form['equipo']
                id_personal_list = request.form.getlist('id_personal')
                id_rol_list = request.form.getlist('rol')

                fecha_hora = datetime.strptime(fecha_hora_str, '%Y-%m-%d')

                nueva_programacion = Programacion(
                    fecha=fecha_hora,
                    id_personal=id_personal,
                    id_area=id_area,
                    id_turno=id_turno,
                    id_vehiculo=id_vehiculo
                )

                db.session.add(nueva_programacion)
                db.session.commit()

                id_programacion = nueva_programacion.id_programacion

                for id_persona, id_rol in zip(id_personal_list, id_rol_list):
                    id_rol = Rol.query.filter_by(id_rol=id_rol).first()
                    if id_rol:
                        personal = Personal.query.filter_by(id_personal=id_persona, estado='Activo').first()
                        if personal:
                            detalle_ep = DetalleEP(
                                id_personal=id_persona,
                                id_rol=id_rol.id_rol,
                                id_programacion=id_programacion,
                            )
                            db.session.add(detalle_ep)

                db.session.commit()

                return redirect(url_for('crear_programacion'))

            supervisores_activos = Personal.query.join(Cargo).filter(Cargo.nombre_cargo == 'Supervisor', Personal.estado == 'Activo').join(DptoEmpresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario, Personal.id_personal >= 1).all()
            personal_equipo = Personal.query.join(Cargo).join(DptoEmpresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario, Personal.id_personal >= 1).all()
            vehiculos = Vehiculo.query.filter(Vehiculo.estado == 'Activo', Vehiculo.id_dpto_empresa == departamento_usuario).all()
            areas = Area.query.filter(Area.tipo_area == 'z_trabajos', Area.id_dpto_empresa == departamento_usuario).all()
            equipos = Equipo.query.filter(Equipo.id_dpto_empresa == departamento_usuario).all()
            turnos = Turno.query.filter(Turno.id_dpto_empresa == departamento_usuario).all()
            roles = Rol.query.filter(Rol.id_dpto_empresa == departamento_usuario).all()
            id_equipo_seleccionado = request.form.get('equipo')

            id_equipo_seleccionado = request.args.get('equipo')
            integrantes_equipo = EquipoPersonal.query.filter_by(id_equipo=id_equipo_seleccionado).all()

            return render_template('datos/crear_programacion.html', equipos=equipos, personales=personal_equipo, personal=supervisores_activos, areas=areas, turnos=turnos, vehiculos=vehiculos, roles=roles, integrantes_equipo=integrantes_equipo)
        else:
            return redirect(url_for('login'))

    # FUNCIONES AREAS
    @app.route('/menu_coordenadas', methods=['GET', 'POST'])
    def menu_coordenadas():
        if 'username' in session:
            return render_template('menu/menu_coordenadas.html')
        else:
            return redirect(url_for('login'))

    @app.route('/ingresar_coordenadas', methods=['GET', 'POST'])
    def ingresar_area_trabajo_route():
        if 'username' in session:
            usuario = Usuario.query.filter_by(username=session['username']).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa

            if request.method == 'POST':
                nombre_area = request.form['nombre_area']
                coordenadas = request.form['coordenadas']
                tipo_area = request.form['tipo_area']
                id_area = request.form['id_area']
                id_dpto_empresa = departamento_usuario

                if tipo_area == 'cuadrantes':
                    areas_trabajo = 'cuadrantes'
                elif tipo_area == 'sectores':
                    areas_trabajo = 'sectores'
                elif tipo_area == 'z_trabajos':
                    areas_trabajo = 'z_trabajos'
                elif tipo_area == 'cercos':
                    areas_trabajo = 'cercos'

                ingresar_area_trabajo(tipo_area, areas_trabajo, nombre_area, coordenadas, id_area, id_dpto_empresa)
                return redirect(url_for('lista_areas'))

            return render_template('datos/crear_coordenadas.html')
        else:
            return redirect(url_for('login'))

    @app.route('/lista_areas')
    def lista_areas():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            lista_areas = Area.query.filter(Area.id_dpto_empresa == departamento_usuario).all()

            return render_template('listas/lista_areas.html', areas=lista_areas)
        else:
            return redirect(url_for('login'))

    @app.route('/menu_area', methods=['GET', 'POST'])
    def menu_area():
        if 'username' in session:
            return render_template('menu/menu_area.html')
        else:
            return redirect(url_for('login'))

    @app.route('/crud_area/<int:id_area>')
    def crud_area(id_area):
        if 'username' in session:
            area = Area.query.get(id_area)
            return render_template('CRUD/area/crud_area.html', area=area)
        else:
            return redirect(url_for('login'))

    @app.route('/eliminar_area/<int:id_area>', methods=['GET', 'POST'])
    def eliminar_area(id_area):
        if 'username' in session:
            area = Area.query.get(id_area)
            if area:
                db.session.delete(area)
                db.session.commit()
            else:
                flash('No se pudo encontrar el área para eliminar.', 'error')
                return redirect(url_for('lista_area'))
        else:
            return redirect(url_for('login'))

    @app.route('/editar_area/<int:id_area>', methods=['GET', 'POST'])
    def editar_area(id_area):
        if 'username' in session:
            area = Area.query.get(id_area)

            # Consulta para cargar las coordenadas de tu área
            coordenadas_area = Coordenadas.query.filter_by(id_area=id_area).all()

            utm = Proj(init='epsg:4326')
            latlon = Proj(init='epsg:4326')
            coordenadas_lat_lon = []

            if request.method == 'POST':
                nombre_area = request.form['nombre_area']
                tipo_area = request.form['tipo_area']
                nuevas_coordenadas = request.form['nuevas_coordenadas']

                area.nombre_area = nombre_area
                area.tipo_area = tipo_area

                Coordenadas.query.filter_by(id_area=id_area).delete()

                coordenadas_lat_lon = [[float(coord[0]), float(coord[1])] for coord in json.loads(nuevas_coordenadas)]
                coordenadas_utm = [transformador.transform(coord[1], coord[0]) for coord in coordenadas_lat_lon]

                for coord_orig, coord_utm in zip(coordenadas_lat_lon, coordenadas_utm):
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
                    flash(f'Error al actualizar el área: {str(e)}', 'error')
                    db.session.rollback()

                return redirect(url_for('lista_areas'))

            # Transforma las coordenadas a latitud y longitud
            for coord in coordenadas_area:
                lat_lon = transform(utm, latlon, coord.grados_latitud, coord.grados_longitud)
                coordenadas_lat_lon.append(lat_lon)

            # Convertir las coordenadas a formato JSON para pasarlas al formulario
            coordenadas_json = json.dumps(coordenadas_lat_lon)

            return render_template('CRUD/area/editar_area.html', area=area, coordenadas_area=coordenadas_lat_lon, coordenadas_json=coordenadas_json)
        else:
            return redirect(url_for('login'))
        
    # FUNCIONES USUARIO
    @app.route('/registrar', methods=['GET', 'POST'])
    def crear_usuario():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                username = request.form['username']
                password_plano = request.form['password']
                rol_usuario = request.form['rol_usuario']
                id_personal = request.form['personal']
                # verificar_token = request.form['verificar_token']

                usuario_existente_username = Usuario.query.filter_by(username=username).first()
                if usuario_existente_username:
                    flash('El nombre de usuario ya está en uso. Por favor, elija otro.')
                    return redirect(url_for('crear_usuario'))

                password_encriptada = generate_password_hash(password_plano)

                nuevo_usuario = Usuario(username=username, 
                                        password=password_encriptada,
                                        id_rol_usuario=rol_usuario,
                                        id_personal=id_personal)
                
                db.session.add(nuevo_usuario)
                db.session.commit()
                
                # if verificar_token == '1':
                #     token = os.urandom(24)
                #     token_hash = hashlib.sha256(token).hexdigest()
                #     nuevo_token = Token(token=token_hash,
                #                         id_usuario=nuevo_usuario.id_usuario)
                #     db.session.add(nuevo_token)
                #     db.session.commit()

                return redirect(url_for('menu_personal'))
            
            rol_usuario = RolUsuario.query.filter(RolUsuario.id_rol_usuario >= 1).all()
            personal = Personal.query.join(Cargo).join(DptoEmpresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario, Personal.id_personal >= 1).all()

            return render_template('auth/register.html', rol_usuario=rol_usuario, personales=personal)
        else:
            return redirect(url_for('login'))

    # FUNCION LOGIN
    @app.route('/', methods=['GET', 'POST'])
    def login():
        if 'username' in session:
            return redirect(url_for('index'))
        else:
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']

                usuario = Usuario.query.filter_by(username=username).first()

                if usuario and check_password_hash(usuario.password, password):
                    session['username'] = usuario.username
                    
                    return redirect(url_for('index'))
                else:
                    return render_template('auth/login.html', error='Usuario o contraseña incorrectos')

            return render_template('auth/login.html')

    # FUNCION LOGOUT
    @app.route('/logout')
    def logout():
        session.pop('username', None)
        return redirect(url_for('login'))

    @app.route('/perfil')
    def perfil():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()

            if usuario and usuario.personal:
                nombre_personal = usuario.personal.nombre_personal + " " + usuario.personal.apellido_paterno + " " + usuario.personal.apellido_materno
                nombre_empresa = usuario.personal.cargo.dpto_empresa.empresa.nombre_empresa
            else:
                nombre_personal = None
                nombre_empresa = None

            return render_template('perfil.html', username=username, 
                                    nombre_personal=nombre_personal, 
                                    nombre_empresa=nombre_empresa)
        else:
            return redirect(url_for('login'))

    # FUNCIONES VEHICULO
    @app.route('/detalles_tv/<int:tipo_vehiculo_id>')
    def detalles_tv(tipo_vehiculo_id):
        if 'username' in session:
            detalles_tv = DetalleTV.query.filter_by(id_tv=tipo_vehiculo_id).all()
            detalles = [{'id_dtv': detalle.id_dtv, 'nombre_dtv': detalle.nombre_dtv} for detalle in detalles_tv]
            return jsonify(detalles)
        else:
            return redirect(url_for('login'))
        
    @app.route('/menu_vehiculo', methods=['GET', 'POST'])
    def menu_vehiculo():
        if 'username' in session:
            return render_template('menu/menu_vehiculo.html')
        else:
            return redirect(url_for('login'))

    @app.route('/crear_vehiculo', methods=['GET', 'POST'])
    def crear_vehiculo():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                flota = request.form['flota']
                patente = request.form['patente']
                gps = request.form['gps']
                estado = request.form['estado']
                restriccion = request.form['restriccion']
                detalle_tv = request.form['detalles_tv']
                
                if 'foto' in request.files:
                    foto = request.files['foto'].read()
                else:
                    foto = None

                nuevo_vehiculo = Vehiculo(
                    id_flota=flota,
                    patente=patente,
                    gps=gps,
                    estado=estado,
                    foto=foto,
                    restriccion=restriccion,
                    id_dtv = detalle_tv,
                    id_dpto_empresa=departamento_usuario
                )

                db.session.add(nuevo_vehiculo)
                db.session.commit()

                return redirect(url_for('lista_vehiculo'))
            tipo_vehiculo = TipoVehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()
            detalles_tv = DetalleTV.query.filter(DetalleTV.id_dtv.in_([tv.id_tv for tv in tipo_vehiculo])).all()
            flota = Flota.query.filter_by(id_dpto_empresa=departamento_usuario).filter(Flota.id_flota >= 1).all()

            return render_template('datos/crear_vehiculo.html', tipo_vehiculo=tipo_vehiculo, flota=flota, detalles_tv=detalles_tv)
        else:
            return redirect(url_for('login'))

    @app.route('/seleccionar_vehiculo', methods=['GET', 'POST'])
    def seleccionar_vehiculo():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            
            if request.method == 'POST':
                seleccion = request.form['seleccion']
                id_vehiculo = request.form['id_vehiculo']
                
                if seleccion == 'Informe':
                    return redirect(url_for('informe_vehiculo', id_vehiculo=id_vehiculo))
                elif seleccion == 'Trayecto':
                    return redirect(url_for('ver_trayecto', id_vehiculo=id_vehiculo))
                else:
                    return render_template('error.html', mensaje='La opción seleccionada no es válida.')

            vehiculos = Vehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()

            return render_template('seleccionar_vehiculo.html', vehiculos=vehiculos)
        else:
            return redirect(url_for('login'))

    @app.route('/informe_vehiculo/<int:id_vehiculo>', methods=['GET', 'POST'])
    def informe_vehiculo(id_vehiculo):
        if 'username' in session:
            fecha_seleccionada = request.form.get('fecha') if request.method == 'POST' else None
            informe_data, vehiculo, fechas_disponibles = obtener_datos_informe(id_vehiculo, fecha_seleccionada)
            if not vehiculo:
                return redirect(url_for('login'))
            return render_template('informe.html', informe_data=informe_data, vehiculo=vehiculo, fecha_seleccionada=fecha_seleccionada, fechas_disponibles=fechas_disponibles)
        else:
            return redirect(url_for('login'))

    @app.route('/api/informe_vehiculo/<int:id_vehiculo>', methods=['GET'])
    def api_informe_vehiculo(id_vehiculo):
        if 'username' in session:
            fecha_seleccionada = 'mostrarTodo'
            informe_data, vehiculo, fechas_disponibles = obtener_datos_informe(id_vehiculo, fecha_seleccionada)
            if not vehiculo:
                return jsonify({'error': 'Vehículo no encontrado'}), 404
            return jsonify({
                'informe_data': informe_data,
                'vehiculo': {
                    'patente': vehiculo.patente,
                },
                'fecha_seleccionada': fecha_seleccionada,
                'fechas_disponibles': list(fechas_disponibles)
            })
        else:
            return jsonify({'error': 'No autenticado'}), 401

    @app.route('/descargar_informe_excel', methods=['POST'])
    def descargar_informe_excel():
        if 'username' in session:
            id_vehiculo = request.form['id_vehiculo']

            # Obtener las coordenadas, fecha, hora y patente del vehículo seleccionado
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

                fecha_anterior = coordenadas_vehiculo[i].fecha  # Actualizar la fecha anterior

            # Convertir los datos del informe en un DataFrame de Pandas
            df = pd.DataFrame(informe_data)

            # Crear un archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                excel_filename = tmp.name

            # Guardar el DataFrame como un archivo Excel
            df.to_excel(excel_filename, index=False)

            # Enviar el archivo como descarga
            return send_file(excel_filename, as_attachment=True, download_name=f'informe_vehiculo_{vehiculo.patente}.xlsx')

        else:
            return redirect(url_for('login'))


    @app.route('/ver_trayecto/<int:id_vehiculo>')
    def ver_trayecto(id_vehiculo):
        if 'username' in session:
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

            # Filtrar las fechas para incluir solo aquellas con coordenadas
            fechas_disponibles = list(reversed(sorted(fechas_con_coordenadas)))

            # Fetch area coordinates with area details
            areas = Area.query.all()
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
            return redirect(url_for('login'))

    @app.route('/crud_vehiculo/<int:id_vehiculo>')
    def crud_vehiculo(id_vehiculo):
        if 'username' in session:
            vehiculo = Vehiculo.query.get(id_vehiculo)
            return render_template('CRUD/vehiculo/crud_vehiculo.html', vehiculo=vehiculo)
        else:
            return redirect(url_for('login'))

    @app.route('/editar_vehiculo/<int:id_vehiculo>', methods=['GET', 'POST'])
    def editar_vehiculo(id_vehiculo):
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            vehiculo = Vehiculo.query.get(id_vehiculo)
            tipo_vehiculo = TipoVehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()
            detalles_tv = DetalleTV.query.filter(DetalleTV.id_dtv.in_([tv.id_tv for tv in tipo_vehiculo])).all()
            flota = Flota.query.filter_by(id_dpto_empresa=departamento_usuario).filter(Flota.id_flota >= 1).all()

            if request.method == 'POST':
                vehiculo.id_flota = request.form['flota']
                vehiculo.patente = request.form['patente']
                vehiculo.gps = request.form['gps']
                vehiculo.estado = request.form['estado']
                vehiculo.restriccion = request.form['restriccion']
                vehiculo.id_dtv = request.form['detalles_tv']

                if 'foto' in request.files:
                    nueva_foto = request.files['foto']
                    if nueva_foto.filename != '':
                        vehiculo.foto = nueva_foto.read()

                db.session.commit()
                return redirect(url_for('lista_vehiculo'))

            return render_template('CRUD/vehiculo/editar_vehiculo.html', vehiculo=vehiculo, tipo_vehiculo=tipo_vehiculo, flota=flota)
        else:
            return redirect(url_for('login'))
        
    @app.route('/eliminar_vehiculo/<int:id_vehiculo>')
    def eliminar_vehiculo(id_vehiculo):
        if 'username' in session:
            vehiculo = Vehiculo.query.get(id_vehiculo)

            if vehiculo:
                CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo).delete()
                db.session.delete(vehiculo)
                db.session.commit()

            return redirect(url_for('lista_vehiculo'))
        else:
            return redirect(url_for('login'))

    @app.route('/carga_masiva_vehiculo', methods=['GET', 'POST'])
    def carga_masiva_vehiculo():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                archivo_excel = request.files['archivo_excel']

                if archivo_excel and archivo_excel.filename.endswith(('.xlsx', '.xls')):
                    # Cargar el archivo Excel sin asumir que la primera fila son los encabezados
                    df = pd.read_excel(archivo_excel, header=None)
                    
                    # Encontrar la fila que contiene 'IMEI' y usarla como encabezado
                    for i, row in df.iterrows():
                        if 'IMEI' in row.values:
                            df.columns = row
                            df = df[i+1:]  # Tomar las filas debajo de la fila de encabezados
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

                        return redirect(url_for('menu_vehiculo'))
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
            return redirect(url_for('login'))

    @app.route('/carga_masiva_coordenadas_vehiculo', methods=['GET', 'POST'])
    def carga_masiva_coordenadas_vehiculo():
        if 'username' in session:
            if request.method == 'POST':
                archivo_excel = request.files['archivo_excel']

                if archivo_excel and archivo_excel.filename.endswith(('.xlsx', '.xls')):
                    # Cargar el archivo Excel sin asumir que la primera fila son los encabezados
                    df = pd.read_excel(archivo_excel, header=None)

                    # Encontrar la fila que contiene 'Longitud' y 'Latitud' y usarla como encabezado
                    for i, row in df.iterrows():
                        if 'Longitud' in row.values and 'Latitud' in row.values:
                            df.columns = row
                            df = df[i+1:]  # Tomar las filas debajo de la fila de encabezados
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

                            # Si es un objeto datetime, formatear directamente
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
                                tipos_de_area, nombres_de_area = coordenada_pertenece_a_areas(row, areas)

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
                                    cuadrante=nombres_de_area[tipos_de_area.index('cuadrantes')] if 'cuadrantes' in tipos_de_area else None,
                                    sector=nombres_de_area[tipos_de_area.index('sectores')] if 'sectores' in tipos_de_area else None,
                                    z_trabajo=nombres_de_area[tipos_de_area.index('z_trabajos')] if 'z_trabajos' in tipos_de_area else None,
                                    cerco=nombres_de_area[tipos_de_area.index('cercos')] if 'cercos' in tipos_de_area else None
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
                        return redirect(url_for('menu_vehiculo'))
                    except IntegrityError as e:
                        print(f"Error de integridad: {e}")
                        return 'Error al guardar las coordenadas del vehículo en la base de datos.', 500
                    except Exception as e:
                        print(f"Error desconocido: {e}")
                        return 'Error al procesar el archivo Excel.', 500
            else:
                return render_template('cargas/carga_masiva_coord_vehiculo.html')
        else:
            return redirect(url_for('login'))

    @app.route('/lista_vehiculo')
    def lista_vehiculo():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            lista_vehiculo = Vehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()

            for vehiculo in lista_vehiculo:
                if vehiculo.foto:
                    vehiculo.foto_encoded = base64.b64encode(vehiculo.foto).decode('utf-8')
                else:
                    vehiculo.foto_encoded = None

            return render_template('listas/lista_vehiculo.html', vehiculo=lista_vehiculo)
        else:
            return redirect(url_for('login'))

    # FUNCIONES PERSONAL
    @app.route('/menu_personal', methods=['GET', 'POST'])
    def menu_personal():
        if 'username' in session:
            return render_template('menu/menu_personal.html')
        else:
            return redirect(url_for('login'))

    @app.route('/crud_personal/<int:id_personal>')
    def crud_personal(id_personal):
        if 'username' in session:
            personal = Personal.query.get(id_personal)
            return render_template('CRUD/personal/crud_personal.html', personal=personal)
        else:
            return redirect(url_for('login'))

    @app.route('/crear_personal', methods=['GET', 'POST'])
    def crear_personal():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            empresa_usuario = usuario.personal.cargo.dpto_empresa.empresa.id_empresa
            if request.method == 'POST':
                rut_personal = request.form['rut_personal']
                nombre_personal = request.form['nombre_personal']
                apellido_paterno = request.form['apellido_paterno']
                apellido_materno = request.form['apellido_materno']
                fecha_contrato = request.form['fecha_contrato']
                fono = request.form['fono']
                estado = request.form['estado']
                id_cargo = request.form['id_cargo']
                
                rut_personal = rut_personal[:-1] + rut_personal[-1].lower() if rut_personal[-1] == 'K' else rut_personal

                if Personal.query.filter_by(rut_personal=rut_personal).first():
                    flash('El rut ingresado ya está en uso. Por favor, ingrese un rut válido.')
                    return redirect(url_for('crear_personal'))

                nuevo_personal = Personal(
                    rut_personal=rut_personal,
                    nombre_personal=nombre_personal,
                    apellido_paterno=apellido_paterno,
                    apellido_materno=apellido_materno,
                    fecha_contrato=fecha_contrato,
                    fono=fono,
                    estado=estado,
                    id_cargo=id_cargo
                )

                db.session.add(nuevo_personal)

                try:
                    db.session.commit()
                    return redirect(url_for('menu_personal'))
                except IntegrityError:
                    db.session.rollback()
                    flash('Error al intentar agregar el personal. Por favor, inténtelo nuevamente.', 'error')

            cargos = Cargo.query.join(DptoEmpresa).filter(DptoEmpresa.id_empresa == empresa_usuario).filter(Cargo.id_cargo >= 1).all()

            return render_template('datos/crear_personal.html', cargos=cargos)
        else:
            return redirect(url_for('login'))

    @app.route('/editar_personal/<int:id_personal>', methods=['GET', 'POST'])
    def editar_personal(id_personal):
        if 'username' in session:
            personal = Personal.query.get(id_personal)
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            empresa_usuario = usuario.personal.cargo.dpto_empresa.empresa.id_empresa

            if request.method == 'POST':

                personal.rut_personal = request.form['rut_personal']
                personal.nombre_personal = request.form['nombre_personal']
                personal.apellido_paterno = request.form['apellido_paterno']
                personal.apellido_materno = request.form['apellido_materno']
                personal.fecha_contrato = request.form['fecha_contrato']
                personal.fono = request.form['fono']
                personal.estado = request.form['estado']
                personal.id_cargo = request.form['id_cargo']

                db.session.commit()
                return redirect(url_for('lista_personal'))

            cargos = Cargo.query.join(DptoEmpresa).filter(DptoEmpresa.id_empresa == empresa_usuario).filter(Cargo.id_cargo >= 1).all()

            return render_template('CRUD/personal/editar_personal.html', personal=personal, cargos=cargos)
        else:
            return redirect(url_for('login'))

    @app.route('/eliminar_personal/<int:id_personal>')
    def eliminar_personal(id_personal):
        if 'username' in session:
            asociaciones_equipo_personal = EquipoPersonal.query.filter_by(id_personal=id_personal).all()

            for asociacion in asociaciones_equipo_personal:
                db.session.delete(asociacion)

            personal = Personal.query.get(id_personal)
            if personal:
                db.session.delete(personal)
                db.session.commit()

            return redirect(url_for('lista_personal'))
        else:
            return redirect(url_for('login'))

    @app.route('/lista_personal')
    def lista_personal():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            personal_usuario = usuario.personal.id_personal
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            lista_personal = Personal.query.join(Cargo).join(DptoEmpresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario, Personal.id_personal >= 1).all()

            return render_template('listas/lista_personal.html', personal=lista_personal)
        else:
            return redirect(url_for('login'))

    # FUNCIONES EQUIPO PERSONAL
    @app.route('/menu_equipo', methods=['GET', 'POST'])
    def menu_equipo():
        if 'username' in session:
            return render_template('menu/menu_equipo.html')
        else:
            return redirect(url_for('login'))
        
    @app.route('/crear_equipo', methods=['GET', 'POST'])
    def crear_equipo():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            personal_usuario = usuario.personal.id_personal
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                nombre_equipo = request.form['nombre_equipo']
                id_personal_list = request.form.getlist('id_personal')

                nuevo_equipo = Equipo(nombre_equipo=nombre_equipo, id_dpto_empresa=departamento_usuario)
                db.session.add(nuevo_equipo)
                db.session.commit()
                id_equipo = nuevo_equipo.id_equipo

                print(f"Nombre: {nombre_equipo}")
                print(f"ID Personal List: {id_personal_list}")

                for id_persona in id_personal_list:
                    personal = Personal.query.filter_by(id_personal=id_persona, estado='Activo').first()
                    if personal:
                        nuevo_equipo_personal = EquipoPersonal(
                            id_equipo=id_equipo,
                            id_personal=id_persona,
                        )
                        db.session.add(nuevo_equipo_personal)

                db.session.commit()

                return redirect(url_for('lista_equipos'))

            personal_activos = Personal.query.join(Cargo).join(DptoEmpresa).join(Empresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario, Personal.estado == 'Activo', Personal.id_personal >= 1).all()

            return render_template('datos/crear_equipo.html', personal=personal_activos)
        else:
            return redirect(url_for('login'))
        
    @app.route('/crud_equipo/<int:id_ep>')
    def crud_equipo(id_ep):
        if 'username' in session:
            equipo = EquipoPersonal.query.get(id_ep)

            if equipo:
                return render_template('CRUD/equipo_personal/crud_equipo.html', equipo=equipo)

            return render_template('ERROR/error.html', mensaje='Equipo no encontrado')
        else:
            return redirect(url_for('login'))

    @app.route('/editar_equipo/<int:id_equipo>', methods=['GET', 'POST'])
    def editar_equipo(id_equipo):
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            personal_usuario = usuario.personal.id_personal
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            
            equipo = Equipo.query.get(id_equipo)
            equipo_personal = EquipoPersonal.query.filter_by(id_equipo=id_equipo).all()

            personal_activos = Personal.query.join(Cargo).join(DptoEmpresa).join(Empresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario, Personal.estado == 'Activo', Personal.id_personal >= 1).all()

            if request.method == 'POST':
                nombre_equipo = request.form['nombre_equipo']
                id_personal_list = request.form.getlist('id_personal')

                equipo.nombre_equipo = nombre_equipo

                for equipo_persona in equipo_personal:
                    db.session.delete(equipo_persona)

                for id_persona in id_personal_list:
                    personal = Personal.query.filter_by(id_personal=id_persona, estado='Activo').first()
                    if personal:
                        nuevo_equipo_personal = EquipoPersonal(
                            id_equipo=id_equipo,
                            id_personal=id_persona
                        )
                        db.session.add(nuevo_equipo_personal)

                db.session.commit()

                return redirect(url_for('lista_equipos'))

            return render_template('CRUD/equipo_personal/editar_equipo.html', equipo=equipo, equipo_personal=equipo_personal, personal=personal_activos)
        else:
            return redirect(url_for('login'))

    @app.route('/eliminar_equipo/<int:id_equipo>')
    def eliminar_equipo(id_equipo):
        if 'username' in session:
            equipos_personales = EquipoPersonal.query.filter_by(id_equipo=id_equipo).all()
            for equipo_personal in equipos_personales:
                db.session.delete(equipo_personal)

            # Eliminar el equipo
            equipo = Equipo.query.get(id_equipo)
            if equipo:
                db.session.delete(equipo)

            db.session.commit()

            return redirect(url_for('lista_equipos'))
        else:
            return redirect(url_for('login'))

    @app.route('/lista_equipos')
    def lista_equipos():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            equipos_con_integrantes = defaultdict(list)

            equipos_personales = EquipoPersonal.query.join(Equipo).filter(or_(Equipo.id_dpto_empresa == departamento_usuario, Equipo.id_dpto_empresa == None)).all()

            for equipo_personal in equipos_personales:
                equipos_con_integrantes[equipo_personal.id_equipo].append(equipo_personal)

            nombres_equipos = {equipo.id_equipo: equipo.nombre_equipo for equipo in Equipo.query.filter(or_(Equipo.id_dpto_empresa == departamento_usuario, Equipo.id_dpto_empresa == None)).all()}

            return render_template('listas/lista_equipos.html', equipos_con_integrantes=equipos_con_integrantes, nombres_equipos=nombres_equipos)
        else:
            return redirect(url_for('login'))

    # FUNCIONES PARAMETROS
    @app.route('/crear_parametro', methods=['GET', 'POST'])
    def crear_parametro():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                nombre_parametro = request.form['nombre_parametro']
                segundos_parametro = int(request.form['segundos_parametro']) * 60
                distancia_parametro = int(request.form['distancia_parametro'])
                velocidad_parametro = float(request.form['velocidad_parametro']) * 3.6

                nuevo_parametro = Parametro(nombre_parametro=nombre_parametro,
                                            segundos_parametro=segundos_parametro,
                                            distancia_parametro=distancia_parametro,
                                            velocidad_parametro=velocidad_parametro,
                                            id_dpto_empresa=departamento_usuario)

                db.session.add(nuevo_parametro)
                db.session.commit()

                return redirect(url_for('crear_parametro'))

            return render_template('datos/crear_parametro.html')
        else:
            return redirect(url_for('login'))

    @app.route('/crud_parametro/<int:id_parametro>')
    def crud_parametro(id_parametro):
        if 'username' in session:
            parametro = Parametro.query.get(id_parametro)

            if parametro:
                return render_template('CRUD/parametro/crud_parametro.html', parametro=parametro)

            return render_template('ERROR/error.html', mensaje='Parametro no encontrado')
        else:
            return redirect(url_for('login'))

    @app.route('/editar_parametro/<int:id_parametro>', methods=['GET', 'POST'])
    def editar_parametro(id_parametro):
        if 'username' in session:
            parametro = Parametro.query.get(id_parametro)

            if request.method == 'POST':
                parametro.nombre_parametro = request.form['nombre_parametro']
                parametro.segundos_parametro = int(request.form['segundos_parametro']) * 60
                parametro.distancia_parametro = int(request.form['distancia_parametro'])
                parametro.velocidad_parametro = float(request.form['velocidad_parametro']) * 3.6

                db.session.commit()
                return redirect(url_for('lista_parametros'))

            return render_template('CRUD/parametro/editar_parametro.html', parametro=parametro)
        else:
            return redirect(url_for('login'))

    @app.route('/eliminar_parametro/<int:id_parametro>')
    def eliminar_parametro(id_parametro):
        if 'username' in session:
            parametro = Parametro.query.get(id_parametro)

            if parametro:
                db.session.delete(parametro)
                db.session.commit()

            return redirect(url_for('lista_parametros'))
        else:
            return redirect(url_for('login'))

    @app.route('/lista_parametros')
    def lista_parametros():
        if 'username' in session:
            lista_parametros = Parametro.query.all()
            return render_template('listas/lista_parametros.html', parametro=lista_parametros)
        else:
            return redirect(url_for('login'))

    # FUNCIONES TIPO VEHICULO
    @app.route('/crear_tipo_vehiculo', methods=['GET', 'POST'])
    def crear_tv():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                nombre_tv = request.form['nombre_tv']
                nuevo_tv = TipoVehiculo(nombre_tv=nombre_tv, id_dpto_empresa=departamento_usuario)

                db.session.add(nuevo_tv)
                db.session.commit()

                return redirect(url_for('lista_tv'))

            return render_template('datos/crear_tipo_vehiculo.html')
        else:
            return redirect(url_for('login'))

    @app.route('/crud_tipo_vehiculo/<int:id_tv>')
    def crud_tv(id_tv):
        if 'username' in session:
            tv = TipoVehiculo.query.get(id_tv)
            if tv:
                return render_template('CRUD/tipo_vehiculo/crud_tipo_vehiculo.html', tv=tv)

            return render_template('ERROR/error.html', mensaje='Tipo no encontrado')
        else:
            return redirect(url_for('login'))

    @app.route('/editar_tipo_vehiculo/<int:id_tv>', methods=['GET', 'POST'])
    def editar_tv(id_tv):
        if 'username' in session:
            tv = TipoVehiculo.query.get(id_tv)

            if request.method == 'POST':
                tv.nombre_tv = request.form['nombre_tv']

                db.session.commit()
                return redirect(url_for('lista_tv'))

            return render_template('CRUD/tipo_vehiculo/editar_tipo_vehiculo.html', tv=tv)
        else:
            return redirect(url_for('login'))

    @app.route('/eliminar_tipo_vehiculo/<int:id_tv>')
    def eliminar_tv(id_tv):
        if 'username' in session:
            tv = TipoVehiculo.query.get(id_tv)

            if tv:
                db.session.delete(tv)
                db.session.commit()

            return redirect(url_for('lista_tv'))
        else:
            return redirect(url_for('login'))
        
    @app.route('/lista_tipo_vehiculos')
    def lista_tv():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            lista_tv = TipoVehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()
            return render_template('listas/lista_tipo_vehiculo.html', tv=lista_tv)
        else:
            return redirect(url_for('login'))

    # FUNCIONES DETALLE TIPO VEHICULO
    @app.route('/crear_detalle_vehiculo', methods=['GET', 'POST'])
    def crear_detalle():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                tipo_vehiculo_id = request.form['tipo_vehiculo']
                nombre_dtv = request.form['nombre_dtv']

                nuevo_detalle_tv = DetalleTV(nombre_dtv=nombre_dtv, id_tv=tipo_vehiculo_id)

                db.session.add(nuevo_detalle_tv)
                db.session.commit()

            tipo_vehiculo = TipoVehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()
            return render_template('datos/crear_detalle_vehiculo.html', tipo_vehiculo=tipo_vehiculo)
        else:
            return redirect(url_for('login'))

    @app.route('/lista_detalle_vehiculo')
    def lista_dtv():
        if 'username' in session:
            usuario = Usuario.query.filter_by(username=session['username']).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            lista_dtv = DetalleTV.query.join(TipoVehiculo).join(DptoEmpresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario).all()
            return render_template('listas/lista_detalle_vehiculo.html', dtv=lista_dtv)
        else:
            return redirect(url_for('login'))

    # FUNCIONES FALLA
    @app.route('/crear_falla', methods=['GET', 'POST'])
    def crear_falla():
        if 'username' in session:
            if request.method == 'POST':
                nombre_falla = request.form['nombre_falla']
                nueva_falla = Falla(nombre_falla=nombre_falla)

                db.session.add(nueva_falla)
                db.session.commit()

                return redirect(url_for('lista_falla'))

            return render_template('datos/crear_falla.html')
        else:
            return redirect(url_for('login'))

    @app.route('/lista_falla')
    def lista_falla():
        if 'username' in session:
            lista_falla = Falla.query.all()
            return render_template('listas/lista_falla.html', fallas=lista_falla)
        else:
            return redirect(url_for('login'))

    # FUNCIONES DETALLE FALLA
    @app.route('/crear_detalle_falla', methods=['GET', 'POST'])
    def crear_detalle_falla():
        if 'username' in session:
            if request.method == 'POST':
                falla = request.form['falla']
                nombre_df = request.form['nombre_df']

                nuevo_df = DetalleFalla(nombre_df=nombre_df, id_falla=falla)

                db.session.add(nuevo_df)
                db.session.commit()

            falla = Falla.query.all()
            return render_template('datos/crear_detalle_falla.html', falla=falla)
        else:
            return redirect(url_for('login'))

    # FUNCIONES FLOTA
    @app.route('/crear_flota', methods=['GET', 'POST'])
    def crear_flota():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            if request.method == 'POST':
                nombre_flota = request.form['nombre_flota']

                nueva_flota = Flota(nombre_flota=nombre_flota, id_dpto_empresa=departamento_usuario)

                db.session.add(nueva_flota)
                db.session.commit()

            return render_template('datos/crear_flota.html')
        else:
            return redirect(url_for('login'))

    # FUNCIONES DEPARTAMENTO EMPRESA
    @app.route('/crear_departamento', methods=['GET', 'POST'])
    def crear_departamento():
        if 'username' in session:
            username = session['username']
            usuario = Usuario.query.filter_by(username=username).first()
            empresa_usuario = usuario.personal.cargo.dpto_empresa.empresa.id_empresa
            if request.method == 'POST':
                nombre_departamento = request.form['nombre_departamento']

                nuevo_departamento = DptoEmpresa(nombre_dpto_empresa=nombre_departamento, id_empresa=empresa_usuario)

                db.session.add(nuevo_departamento)
                db.session.commit()

            return render_template('datos/crear_departamento.html')
        else:
            return redirect(url_for('login'))

    # FUNCIONES ROL DE USUARIO
    @app.route('/crear_rol_usuario', methods=['GET', 'POST'])
    def crear_rol_usuario():
        if 'username' in session:
            if request.method == 'POST':
                nombre_rol_usuario = request.form['nombre_rol_usuario']
                nuevo_rol_usuario = RolUsuario(nombre_rol_usuario=nombre_rol_usuario)

                db.session.add(nuevo_rol_usuario)
                db.session.commit()

                return redirect(url_for('lista_rol_usuario'))

            return render_template('datos/crear_rol_usuario.html')
        else:
            return redirect(url_for('login'))
        
    @app.route('/lista_rol_usuario')
    def lista_rol_usuario():
        if 'username' in session:
            lista_rol_usuario = RolUsuario.query.filter(RolUsuario.id_rol_usuario >= 1).all()
            return render_template('listas/lista_rol_usuario.html', rol_usuario=lista_rol_usuario)
        else:
            return redirect(url_for('login'))