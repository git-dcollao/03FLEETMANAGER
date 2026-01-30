from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from app.db import db 
from app.models import Usuario, Cargo, Rol, Turno, Programacion, Personal, Vehiculo, Area, Coordenadas, DetalleEP, DptoEmpresa, EquipoPersonal, Equipo, RolUsuario, Flota, Falla, DetalleFalla, TipoVehiculo, DetalleTV, Parametro, Empresa
from app.funciones import ingresar_area_trabajo
from datetime import datetime
from sqlalchemy.exc import IntegrityError

creation = Blueprint('creation', __name__)

@creation.route('/crear_cargo', methods=['GET', 'POST'])
def crear_cargo():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        empresa_usuario = usuario.personal.cargo.dpto_empresa.empresa.id_empresa
        
        if request.method == 'POST':
            nombre_cargo = request.form['nombre_cargo']
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            nuevo_cargo = Cargo(nombre_cargo=nombre_cargo, 
                                id_dpto_empresa=departamento_usuario)

            db.session.add(nuevo_cargo)
            db.session.commit()

            return redirect(url_for('creation.crear_cargo'))
        
        cargos = Cargo.query.join(DptoEmpresa).filter(DptoEmpresa.id_empresa == empresa_usuario).all()
        return render_template('datos/crear_cargo.html', cargos=cargos, empresa_usuario=empresa_usuario, username=username)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_rol', methods=['GET', 'POST'])
def crear_rol():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        empresa_usuario = usuario.personal.cargo.dpto_empresa.empresa.id_empresa

        if request.method == 'POST':
            departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
            nombre_rol = request.form['nombre_rol']
            nuevo_rol = Rol(nombre_rol=nombre_rol, 
                            id_dpto_empresa=departamento_usuario)

            db.session.add(nuevo_rol)
            db.session.commit()

            return redirect(url_for('creation.crear_rol'))

        roles = Rol.query.join(DptoEmpresa).filter(DptoEmpresa.id_empresa == empresa_usuario).all()
        return render_template('datos/crear_rol.html', roles=roles, empresa_usuario=empresa_usuario, username=username)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_turno', methods=['GET', 'POST'])
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

            return redirect(url_for('creation.crear_turno'))

        return render_template('datos/crear_turno.html', username=session['username'])
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_programacion', methods=['GET', 'POST'])
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

            return redirect(url_for('creation.crear_programacion'))

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
        return redirect(url_for('auth.login'))

@creation.route('/crear_rol_usuario', methods=['GET', 'POST'])
def crear_rol_usuario():
    if 'username' in session:
        if request.method == 'POST':
            nombre_rol_usuario = request.form['nombre_rol_usuario']
            nuevo_rol_usuario = RolUsuario(nombre_rol_usuario=nombre_rol_usuario)

            db.session.add(nuevo_rol_usuario)
            db.session.commit()

            return redirect(url_for('creation.crear_rol_usuario'))
        
        roles_usuario = RolUsuario.query.all()
        return render_template('datos/crear_rol_usuario.html', roles_usuario=roles_usuario)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_flota', methods=['GET', 'POST'])
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
            return redirect(url_for('creation.crear_flota'))
        
        flotas = Flota.query.filter_by(id_dpto_empresa=departamento_usuario).all()
        return render_template('datos/crear_flota.html', flotas=flotas, departamento_usuario=departamento_usuario)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_departamento', methods=['GET', 'POST'])
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
            return redirect(url_for('creation.crear_departamento'))

        departamentos = DptoEmpresa.query.filter_by(id_empresa=empresa_usuario).all()
        return render_template('datos/crear_departamento.html', departamentos=departamentos, empresa_usuario=empresa_usuario, username=username)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_detalle_falla', methods=['GET', 'POST'])
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
        return redirect(url_for('auth.login'))

@creation.route('/crear_falla', methods=['GET', 'POST'])
def crear_falla():
    if 'username' in session:
        if request.method == 'POST':
            nombre_falla = request.form['nombre_falla']
            nueva_falla = Falla(nombre_falla=nombre_falla)

            db.session.add(nueva_falla)
            db.session.commit()

            return redirect(url_for('crud.lista_falla'))

        return render_template('datos/crear_falla.html')
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_detalle_vehiculo', methods=['GET', 'POST'])
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
        return redirect(url_for('auth.login'))

@creation.route('/crear_tipo_vehiculo', methods=['GET', 'POST'])
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
            return redirect(url_for('creation.crear_tv'))
        
        tipos_vehiculo = TipoVehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()
        return render_template('datos/crear_tipo_vehiculo.html', tipos_vehiculo=tipos_vehiculo)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_parametro', methods=['GET', 'POST'])
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

            return redirect(url_for('creation.crear_parametro'))

        return render_template('datos/crear_parametro.html')
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_equipo', methods=['GET', 'POST'])
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

            return redirect(url_for('crud.lista_equipos'))

        personal_activos = Personal.query.join(Cargo).join(DptoEmpresa).join(Empresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario, Personal.estado == 'Activo', Personal.id_personal >= 1).all()

        return render_template('datos/crear_equipo.html', personal=personal_activos)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_personal', methods=['GET', 'POST'])
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
                return redirect(url_for('creation.crear_personal'))

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
                return redirect(url_for('main.menu_personal'))
            except IntegrityError:
                db.session.rollback()
                flash('Error al intentar agregar el personal. Por favor, inténtelo nuevamente.', 'error')

        cargos = Cargo.query.join(DptoEmpresa).filter(DptoEmpresa.id_empresa == empresa_usuario).filter(Cargo.id_cargo >= 1).all()

        return render_template('datos/crear_personal.html', cargos=cargos)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/ingresar_coordenadas', methods=['GET', 'POST'])
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
            return redirect(url_for('crud.lista_areas'))

        return render_template('datos/crear_coordenadas.html')
    else:
        return redirect(url_for('auth.login'))

@creation.route('/ingresar_coordenadas_all', methods=['GET', 'POST'])
def ingresar_area_trabajo_route_all():
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
            return redirect(url_for('crud.lista_areas'))

        # Obtener áreas existentes por tipo
        cuadrantes = Area.query.filter_by(tipo_area='cuadrantes', id_dpto_empresa=departamento_usuario).all()
        sectores = Area.query.filter_by(tipo_area='sectores', id_dpto_empresa=departamento_usuario).all()
        zonas = Area.query.filter_by(tipo_area='z_trabajos', id_dpto_empresa=departamento_usuario).all()
        cercos = Area.query.filter_by(tipo_area='cercos', id_dpto_empresa=departamento_usuario).all()

        # Convertir coordenadas a JSON
        import json
        areas_data = {
            'cuadrantes': [{
                'id': a.id_area,
                'nombre': a.nombre_area,
                'coordenadas': [[float(c.grados_latitud), float(c.grados_longitud)] for c in sorted(a.coordenadas, key=lambda x: x.id_coordenadas)]
            } for a in cuadrantes],
            'sectores': [{
                'id': a.id_area,
                'nombre': a.nombre_area,
                'coordenadas': [[float(c.grados_latitud), float(c.grados_longitud)] for c in sorted(a.coordenadas, key=lambda x: x.id_coordenadas)]
            } for a in sectores],
            'z_trabajos': [{
                'id': a.id_area,
                'nombre': a.nombre_area,
                'coordenadas': [[float(c.grados_latitud), float(c.grados_longitud)] for c in sorted(a.coordenadas, key=lambda x: x.id_coordenadas)]
            } for a in zonas],
            'cercos': [{
                'id': a.id_area,
                'nombre': a.nombre_area,
                'coordenadas': [[float(c.grados_latitud), float(c.grados_longitud)] for c in sorted(a.coordenadas, key=lambda x: x.id_coordenadas)]
            } for a in cercos]
        }

        areas_json = json.dumps(areas_data, ensure_ascii=False, default=str)
        print(f"DEBUG: Areas JSON: {areas_json[:200]}")  # Primeros 200 caracteres
        return render_template('datos/crear_coordenadas_all.html', areas_json=areas_json)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/api/areas_json', methods=['GET'])
def get_areas_json():
    """Endpoint de debugging para ver el JSON de áreas"""
    if 'username' in session:
        usuario = Usuario.query.filter_by(username=session['username']).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        
        # Obtener áreas existentes por tipo
        cuadrantes = Area.query.filter_by(tipo_area='cuadrantes', id_dpto_empresa=departamento_usuario).all()
        sectores = Area.query.filter_by(tipo_area='sectores', id_dpto_empresa=departamento_usuario).all()
        zonas = Area.query.filter_by(tipo_area='z_trabajos', id_dpto_empresa=departamento_usuario).all()
        cercos = Area.query.filter_by(tipo_area='cercos', id_dpto_empresa=departamento_usuario).all()

        import json
        areas_data = {
            'cuadrantes': [{
                'id': a.id_area,
                'nombre': a.nombre_area,
                'coordenadas': [[float(c.grados_latitud), float(c.grados_longitud)] for c in a.coordenadas]
            } for a in cuadrantes],
            'sectores': [{
                'id': a.id_area,
                'nombre': a.nombre_area,
                'coordenadas': [[float(c.grados_latitud), float(c.grados_longitud)] for c in a.coordenadas]
            } for a in sectores],
            'z_trabajos': [{
                'id': a.id_area,
                'nombre': a.nombre_area,
                'coordenadas': [[float(c.grados_latitud), float(c.grados_longitud)] for c in a.coordenadas]
            } for a in zonas],
            'cercos': [{
                'id': a.id_area,
                'nombre': a.nombre_area,
                'coordenadas': [[float(c.grados_latitud), float(c.grados_longitud)] for c in a.coordenadas]
            } for a in cercos]
        }
        
        return json.dumps(areas_data, ensure_ascii=False, default=str)
    else:
        return json.dumps({"error": "Not logged in"})

@creation.route('/api/update_area_coordinates', methods=['POST'])
def update_area_coordinates():
    """Actualizar coordenadas de un área"""
    if 'username' not in session:
        return {'success': False, 'error': 'No autenticado'}, 401
    
    try:
        data = request.get_json()
        area_id = data.get('area_id')
        coordinates = data.get('coordinates')  # [[lat, lng], [lat, lng], ...]
        
        # Validar datos
        if not area_id or not coordinates or len(coordinates) < 3:
            return {'success': False, 'error': 'Datos inválidos'}, 400
        
        # Obtener el área
        area = Area.query.filter_by(id_area=area_id).first()
        if not area:
            return {'success': False, 'error': 'Área no encontrada'}, 404
        
        # Verificar permiso (usuario debe pertenecer al mismo departamento)
        usuario = Usuario.query.filter_by(username=session['username']).first()
        if area.id_dpto_empresa != usuario.personal.cargo.dpto_empresa.id_dpto_empresa:
            return {'success': False, 'error': 'No tienes permiso para editar esta área'}, 403
        
        # Eliminar coordenadas antiguas
        Coordenadas.query.filter_by(id_area=area_id).delete()
        
        # Asegurar que el polígono sea cerrado (último punto = primer punto)
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        
        # Agregar nuevas coordenadas
        for idx, coord in enumerate(coordinates):
            lat, lng = coord[0], coord[1]
            nueva_coord = Coordenadas(
                latitud=lat,
                longitud=lng,
                grados_latitud=lat,
                grados_longitud=lng,
                id_area=area_id
            )
            db.session.add(nueva_coord)
        
        db.session.commit()
        
        return {'success': True, 'message': 'Coordenadas actualizadas exitosamente'}, 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error actualizando coordenadas: {str(e)}")
        return {'success': False, 'error': str(e)}, 500
    
@creation.route('/crear_vehiculo', methods=['GET', 'POST'])
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

            return redirect(url_for('creation.crear_vehiculo'))
        tipo_vehiculo = TipoVehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()
        detalles_tv = DetalleTV.query.filter(DetalleTV.id_dtv.in_([tv.id_tv for tv in tipo_vehiculo])).all()
        flota = Flota.query.filter_by(id_dpto_empresa=departamento_usuario).filter(Flota.id_flota >= 1).all()
        vehiculos_existentes = Vehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()

        return render_template('datos/crear_vehiculo.html', tipo_vehiculo=tipo_vehiculo, flota=flota, detalles_tv=detalles_tv, vehiculos_existentes=vehiculos_existentes)
    else:
        return redirect(url_for('auth.login'))

@creation.route('/crear_empresa', methods=['GET', 'POST'])
def crear_empresa():
    if 'username' in session:
        if request.method == 'POST':
            nombre_empresa = request.form.get('nombre_empresa', '').strip()
            
            if not nombre_empresa:
                flash('El nombre de la empresa es requerido', 'error')
                return redirect(url_for('creation.crear_empresa'))
            
            try:
                nueva_empresa = Empresa(nombre_empresa=nombre_empresa)
                db.session.add(nueva_empresa)
                db.session.commit()
                flash('Empresa creada exitosamente', 'success')
                return redirect(url_for('crud.lista_empresas'))
            except IntegrityError:
                db.session.rollback()
                flash('Esta empresa ya existe', 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al crear la empresa: {str(e)}', 'error')
        
        return render_template('datos/crear_empresa.html')
    else:
        return redirect(url_for('auth.login'))