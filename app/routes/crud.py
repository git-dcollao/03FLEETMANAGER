from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request, flash
from app.db import db 
from app.models import Usuario, DetalleTV, Vehiculo, TipoVehiculo, Flota, Personal, CoordenadasVehiculo, DptoEmpresa, Cargo, EquipoPersonal, Equipo, Empresa, Parametro, Falla, RolUsuario, Area, Coordenadas, Rol
from app.funciones import transformador
from collections import defaultdict
from sqlalchemy import or_
from pyproj import Proj, transform
import base64
import json

crud = Blueprint('crud', __name__)

@crud.route('/detalles_tv/<int:tipo_vehiculo_id>')
def detalles_tv(tipo_vehiculo_id):
    if 'username' in session:
        detalles_tv = DetalleTV.query.filter_by(id_tv=tipo_vehiculo_id).all()
        detalles = [{'id_dtv': detalle.id_dtv, 'nombre_dtv': detalle.nombre_dtv} for detalle in detalles_tv]
        return jsonify(detalles)
    else:
        return redirect(url_for('auth.login'))
    
@crud.route('/crud_vehiculo/<int:id_vehiculo>')
def crud_vehiculo(id_vehiculo):
    if 'username' in session:
        vehiculo = Vehiculo.query.get(id_vehiculo)
        return render_template('CRUD/vehiculo/crud_vehiculo.html', vehiculo=vehiculo)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_vehiculo/<int:id_vehiculo>', methods=['GET', 'POST'])
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
            return redirect(url_for('crud.lista_vehiculo'))

        return render_template('CRUD/vehiculo/editar_vehiculo.html', vehiculo=vehiculo, tipo_vehiculo=tipo_vehiculo, flota=flota)
    else:
        return redirect(url_for('auth.login'))
    
@crud.route('/eliminar_vehiculo/<int:id_vehiculo>')
def eliminar_vehiculo(id_vehiculo):
    if 'username' in session:
        vehiculo = Vehiculo.query.get(id_vehiculo)

        if vehiculo:
            CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo).delete()
            db.session.delete(vehiculo)
            db.session.commit()

        return redirect(url_for('crud.lista_vehiculo'))
    else:
        return redirect(url_for('auth.login'))

@crud.route('/lista_vehiculo')
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
        return redirect(url_for('auth.login'))

@crud.route('/crud_personal/<int:id_personal>')
def crud_personal(id_personal):
    if 'username' in session:
        personal = Personal.query.get(id_personal)
        return render_template('CRUD/personal/crud_personal.html', personal=personal)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_personal/<int:id_personal>', methods=['GET', 'POST'])
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
            return redirect(url_for('crud.lista_personal'))

        cargos = Cargo.query.join(DptoEmpresa).filter(DptoEmpresa.id_empresa == empresa_usuario).filter(Cargo.id_cargo >= 1).all()

        return render_template('CRUD/personal/editar_personal.html', personal=personal, cargos=cargos)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_personal/<int:id_personal>')
def eliminar_personal(id_personal):
    if 'username' in session:
        asociaciones_equipo_personal = EquipoPersonal.query.filter_by(id_personal=id_personal).all()

        for asociacion in asociaciones_equipo_personal:
            db.session.delete(asociacion)

        personal = Personal.query.get(id_personal)
        if personal:
            db.session.delete(personal)
            db.session.commit()

        return redirect(url_for('crud.lista_personal'))
    else:
        return redirect(url_for('auth.login'))

@crud.route('/lista_personal')
def lista_personal():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        personal_usuario = usuario.personal.id_personal
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        lista_personal = Personal.query.join(Cargo).join(DptoEmpresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario, Personal.id_personal >= 1).all()

        return render_template('listas/lista_personal.html', personal=lista_personal)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/crud_equipo/<int:id_ep>')
def crud_equipo(id_ep):
    if 'username' in session:
        equipo = EquipoPersonal.query.get(id_ep)

        if equipo:
            return render_template('CRUD/equipo_personal/crud_equipo.html', equipo=equipo)

        return render_template('ERROR/error.html', mensaje='Equipo no encontrado')
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_equipo/<int:id_equipo>', methods=['GET', 'POST'])
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

            return redirect(url_for('crud.lista_equipos'))

        return render_template('CRUD/equipo_personal/editar_equipo.html', equipo=equipo, equipo_personal=equipo_personal, personal=personal_activos)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_equipo/<int:id_equipo>')
def eliminar_equipo(id_equipo):
    if 'username' in session:
        equipos_personales = EquipoPersonal.query.filter_by(id_equipo=id_equipo).all()
        for equipo_personal in equipos_personales:
            db.session.delete(equipo_personal)

        equipo = Equipo.query.get(id_equipo)
        if equipo:
            db.session.delete(equipo)

        db.session.commit()

        return redirect(url_for('crud.lista_equipos'))
    else:
        return redirect(url_for('auth.login'))

@crud.route('/lista_equipos')
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
        return redirect(url_for('auth.login'))

@crud.route('/crud_parametro/<int:id_parametro>')
def crud_parametro(id_parametro):
    if 'username' in session:
        parametro = Parametro.query.get(id_parametro)

        if parametro:
            return render_template('CRUD/parametro/crud_parametro.html', parametro=parametro)

        return render_template('ERROR/error.html', mensaje='Parametro no encontrado')
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_parametro/<int:id_parametro>', methods=['GET', 'POST'])
def editar_parametro(id_parametro):
    if 'username' in session:
        parametro = Parametro.query.get(id_parametro)

        if request.method == 'POST':
            parametro.nombre_parametro = request.form['nombre_parametro']
            parametro.segundos_parametro = int(request.form['segundos_parametro']) * 60
            parametro.distancia_parametro = int(request.form['distancia_parametro'])
            parametro.velocidad_parametro = float(request.form['velocidad_parametro']) * 3.6

            db.session.commit()
            return redirect(url_for('crud.lista_parametros'))

        return render_template('CRUD/parametro/editar_parametro.html', parametro=parametro)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_parametro/<int:id_parametro>')
def eliminar_parametro(id_parametro):
    if 'username' in session:
        parametro = Parametro.query.get(id_parametro)

        if parametro:
            db.session.delete(parametro)
            db.session.commit()

        return redirect(url_for('crud.lista_parametros'))
    else:
        return redirect(url_for('auth.login'))

@crud.route('/lista_parametros')
def lista_parametros():
    if 'username' in session:
        lista_parametros = Parametro.query.all()
        return render_template('listas/lista_parametros.html', parametro=lista_parametros)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/crud_tipo_vehiculo/<int:id_tv>')
def crud_tv(id_tv):
    if 'username' in session:
        tv = TipoVehiculo.query.get(id_tv)
        if tv:
            return render_template('CRUD/tipo_vehiculo/crud_tipo_vehiculo.html', tv=tv)

        return render_template('ERROR/error.html', mensaje='Tipo no encontrado')
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_tipo_vehiculo/<int:id_tv>', methods=['GET', 'POST'])
def editar_tv(id_tv):
    if 'username' in session:
        tv = TipoVehiculo.query.get(id_tv)

        if request.method == 'POST':
            tv.nombre_tv = request.form['nombre_tv']

            db.session.commit()
            return redirect(url_for('crud.lista_tv'))

        return render_template('CRUD/tipo_vehiculo/editar_tipo_vehiculo.html', tv=tv)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_tipo_vehiculo/<int:id_tv>')
def eliminar_tv(id_tv):
    if 'username' in session:
        tv = TipoVehiculo.query.get(id_tv)

        if tv:
            db.session.delete(tv)
            db.session.commit()

        return redirect(url_for('crud.lista_tv'))
    else:
        return redirect(url_for('auth.login'))
    
@crud.route('/lista_tipo_vehiculos')
def lista_tv():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        lista_tv = TipoVehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()
        return render_template('listas/lista_tipo_vehiculo.html', tv=lista_tv)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/lista_detalle_vehiculo')
def lista_dtv():
    if 'username' in session:
        usuario = Usuario.query.filter_by(username=session['username']).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        lista_dtv = DetalleTV.query.join(TipoVehiculo).join(DptoEmpresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario).all()
        return render_template('listas/lista_detalle_vehiculo.html', dtv=lista_dtv)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/lista_falla')
def lista_falla():
    if 'username' in session:
        lista_falla = Falla.query.all()
        return render_template('listas/lista_falla.html', fallas=lista_falla)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/lista_rol_usuario')
def lista_rol_usuario():
    if 'username' in session:
        lista_rol_usuario = RolUsuario.query.filter(RolUsuario.id_rol_usuario >= 1).all()
        return render_template('listas/lista_rol_usuario.html', rol_usuario=lista_rol_usuario)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/lista_areas')
def lista_areas():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        lista_areas = Area.query.filter(Area.id_dpto_empresa == departamento_usuario).all()

        return render_template('listas/lista_areas.html', areas=lista_areas)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/crud_area/<int:id_area>')
def crud_area(id_area):
    if 'username' in session:
        area = Area.query.get(id_area)
        return render_template('CRUD/area/crud_area.html', area=area)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_area/<int:id_area>', methods=['GET', 'POST'])
def eliminar_area(id_area):
    if 'username' in session:
        area = Area.query.get(id_area)
        if area:
            db.session.delete(area)
            db.session.commit()
        else:
            flash('No se pudo encontrar el área para eliminar.', 'error')
            return redirect(url_for('crud.lista_areas'))
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_area/<int:id_area>', methods=['GET', 'POST'])
def editar_area(id_area):
    if 'username' in session:
        area = Area.query.get(id_area)

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

            return redirect(url_for('crud.lista_areas'))

        for coord in coordenadas_area:
            lat_lon = transform(utm, latlon, coord.grados_latitud, coord.grados_longitud)
            coordenadas_lat_lon.append(lat_lon)

        coordenadas_json = json.dumps(coordenadas_lat_lon)

        return render_template('CRUD/area/editar_area.html', area=area, coordenadas_area=coordenadas_lat_lon, coordenadas_json=coordenadas_json)
    else:
        return redirect(url_for('auth.login'))

# ==================== CRUD EMPRESA ====================

@crud.route('/crud_empresa/<int:id_empresa>')
def crud_empresa(id_empresa):
    if 'username' in session:
        empresa = Empresa.query.get(id_empresa)
        return render_template('CRUD/empresa/crud_empresa.html', empresa=empresa)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_empresa/<int:id_empresa>', methods=['GET', 'POST'])
def editar_empresa(id_empresa):
    if 'username' in session:
        empresa = Empresa.query.get(id_empresa)
        
        if request.method == 'POST':
            empresa.nombre_empresa = request.form['nombre_empresa']
            
            try:
                db.session.commit()
                flash('Empresa actualizada exitosamente', 'success')
                return redirect(url_for('crud.lista_empresas'))
            except Exception as e:
                flash(f'Error al actualizar la empresa: {str(e)}', 'error')
                db.session.rollback()

        return render_template('CRUD/empresa/editar_empresa.html', empresa=empresa)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_empresa/<int:id_empresa>')
def eliminar_empresa(id_empresa):
    if 'username' in session:
        try:
            empresa = Empresa.query.get(id_empresa)
            if empresa:
                db.session.delete(empresa)
                db.session.commit()
                flash('Empresa eliminada exitosamente', 'success')
            return redirect(url_for('crud.lista_empresas'))
        except Exception as e:
            flash(f'Error al eliminar la empresa: {str(e)}', 'error')
            db.session.rollback()
            return redirect(url_for('crud.lista_empresas'))
    else:
        return redirect(url_for('auth.login'))

@crud.route('/lista_empresas')
def lista_empresas():
    if 'username' in session:
        empresas = Empresa.query.all()
        return render_template('listas/lista_empresas.html', empresas=empresas)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/api/crear_empresa_ajax', methods=['POST'])
def crear_empresa_ajax():
    if 'username' in session:
        nombre_empresa = request.form.get('nombre_empresa', '').strip()
        
        if not nombre_empresa:
            return jsonify({'success': False, 'message': 'El nombre es requerido'}), 400
        
        try:
            nueva_empresa = Empresa(nombre_empresa=nombre_empresa)
            db.session.add(nueva_empresa)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Empresa creada exitosamente',
                'empresa': {
                    'id_empresa': nueva_empresa.id_empresa,
                    'nombre_empresa': nueva_empresa.nombre_empresa
                }
            }), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Esta empresa ya existe'}), 409
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
# ==================== CRUD FLOTA ====================

@crud.route('/api/crear_flota_ajax', methods=['POST'])
def crear_flota_ajax():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        
        nombre_flota = request.form.get('nombre_flota', '').strip()
        
        if not nombre_flota:
            return jsonify({'success': False, 'message': 'El nombre de la flota es requerido'}), 400
        
        try:
            nueva_flota = Flota(nombre_flota=nombre_flota, id_dpto_empresa=departamento_usuario)
            db.session.add(nueva_flota)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Flota creada exitosamente',
                'flota': {
                    'id_flota': nueva_flota.id_flota,
                    'nombre_flota': nueva_flota.nombre_flota
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

@crud.route('/crud_flota/<int:id_flota>')
def crud_flota(id_flota):
    if 'username' in session:
        flota = Flota.query.get(id_flota)
        return render_template('CRUD/flota/crud_flota.html', flota=flota)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_flota/<int:id_flota>', methods=['GET', 'POST'])
def editar_flota(id_flota):
    if 'username' in session:
        flota = Flota.query.get(id_flota)
        
        if request.method == 'POST':
            flota.nombre_flota = request.form['nombre_flota']
            
            try:
                db.session.commit()
                flash('Flota actualizada exitosamente', 'success')
                return redirect(url_for('creation.crear_flota'))
            except Exception as e:
                flash(f'Error al actualizar la flota: {str(e)}', 'error')
                db.session.rollback()

        return render_template('CRUD/flota/editar_flota.html', flota=flota)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_flota/<int:id_flota>')
def eliminar_flota(id_flota):
    if 'username' in session:
        try:
            flota = Flota.query.get(id_flota)
            if flota:
                db.session.delete(flota)
                db.session.commit()
                flash('Flota eliminada exitosamente', 'success')
            return redirect(url_for('creation.crear_flota'))
        except Exception as e:
            flash(f'Error al eliminar la flota: {str(e)}', 'error')
            db.session.rollback()
            return redirect(url_for('creation.crear_flota'))
    else:
        return redirect(url_for('auth.login'))

# ==================== CRUD CARGO ====================

@crud.route('/api/crear_cargo_ajax', methods=['POST'])
def crear_cargo_ajax():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        
        nombre_cargo = request.form.get('nombre_cargo', '').strip()
        
        if not nombre_cargo:
            return jsonify({'success': False, 'message': 'El nombre del cargo es requerido'}), 400
        
        try:
            nuevo_cargo = Cargo(nombre_cargo=nombre_cargo, id_dpto_empresa=departamento_usuario)
            db.session.add(nuevo_cargo)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Cargo creado exitosamente',
                'cargo': {
                    'id_cargo': nuevo_cargo.id_cargo,
                    'nombre_cargo': nuevo_cargo.nombre_cargo
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

@crud.route('/crud_cargo/<int:id_cargo>')
def crud_cargo(id_cargo):
    if 'username' in session:
        cargo = Cargo.query.get(id_cargo)
        return render_template('CRUD/cargo/crud_cargo.html', cargo=cargo)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_cargo/<int:id_cargo>', methods=['GET', 'POST'])
def editar_cargo(id_cargo):
    if 'username' in session:
        cargo = Cargo.query.get(id_cargo)
        
        if request.method == 'POST':
            cargo.nombre_cargo = request.form['nombre_cargo']
            
            try:
                db.session.commit()
                flash('Cargo actualizado exitosamente', 'success')
                return redirect(url_for('creation.crear_cargo'))
            except Exception as e:
                flash(f'Error al actualizar el cargo: {str(e)}', 'error')
                db.session.rollback()

        return render_template('CRUD/cargo/editar_cargo.html', cargo=cargo)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_cargo/<int:id_cargo>')
def eliminar_cargo(id_cargo):
    if 'username' in session:
        try:
            cargo = Cargo.query.get(id_cargo)
            if cargo:
                db.session.delete(cargo)
                db.session.commit()
                flash('Cargo eliminado exitosamente', 'success')
            return redirect(url_for('creation.crear_cargo'))
        except Exception as e:
            flash(f'Error al eliminar el cargo: {str(e)}', 'error')
            db.session.rollback()
            return redirect(url_for('creation.crear_cargo'))
    else:
        return redirect(url_for('auth.login'))

# ==================== CRUD DEPARTAMENTO ====================

@crud.route('/api/crear_departamento_ajax', methods=['POST'])
def crear_departamento_ajax():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        empresa_usuario = usuario.personal.cargo.dpto_empresa.empresa.id_empresa
        
        nombre_departamento = request.form.get('nombre_dpto_empresa', '').strip()
        
        if not nombre_departamento:
            return jsonify({'success': False, 'message': 'El nombre del departamento es requerido'}), 400
        
        try:
            nuevo_departamento = DptoEmpresa(nombre_dpto_empresa=nombre_departamento, id_empresa=empresa_usuario)
            db.session.add(nuevo_departamento)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Departamento creado exitosamente',
                'departamento': {
                    'id_dpto_empresa': nuevo_departamento.id_dpto_empresa,
                    'nombre_dpto_empresa': nuevo_departamento.nombre_dpto_empresa
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

@crud.route('/crud_departamento/<int:id_dpto_empresa>')
def crud_departamento(id_dpto_empresa):
    if 'username' in session:
        departamento = DptoEmpresa.query.get(id_dpto_empresa)
        return render_template('CRUD/departamento/crud_departamento.html', departamento=departamento)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_departamento/<int:id_dpto_empresa>', methods=['GET', 'POST'])
def editar_departamento(id_dpto_empresa):
    if 'username' in session:
        departamento = DptoEmpresa.query.get(id_dpto_empresa)
        
        if request.method == 'POST':
            departamento.nombre_dpto_empresa = request.form['nombre_dpto_empresa']
            
            try:
                db.session.commit()
                flash('Departamento actualizado exitosamente', 'success')
                return redirect(url_for('creation.crear_departamento'))
            except Exception as e:
                flash(f'Error al actualizar el departamento: {str(e)}', 'error')
                db.session.rollback()

        return render_template('CRUD/departamento/editar_departamento.html', departamento=departamento)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_departamento/<int:id_dpto_empresa>')
def eliminar_departamento(id_dpto_empresa):
    if 'username' in session:
        try:
            departamento = DptoEmpresa.query.get(id_dpto_empresa)
            if departamento:
                db.session.delete(departamento)
                db.session.commit()
                flash('Departamento eliminado exitosamente', 'success')
            return redirect(url_for('creation.crear_departamento'))
        except Exception as e:
            flash(f'Error al eliminar el departamento: {str(e)}', 'error')
            db.session.rollback()
            return redirect(url_for('creation.crear_departamento'))
    else:
        return redirect(url_for('auth.login'))

# ==================== CRUD ROL ====================

@crud.route('/api/crear_rol_ajax', methods=['POST'])
def crear_rol_ajax():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        
        nombre_rol = request.form.get('nombre_rol', '').strip()
        
        if not nombre_rol:
            return jsonify({'success': False, 'message': 'El nombre del rol es requerido'}), 400
        
        try:
            nuevo_rol = Rol(nombre_rol=nombre_rol, id_dpto_empresa=departamento_usuario)
            db.session.add(nuevo_rol)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Rol creado exitosamente',
                'rol': {
                    'id_rol': nuevo_rol.id_rol,
                    'nombre_rol': nuevo_rol.nombre_rol
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

@crud.route('/crud_rol/<int:id_rol>')
def crud_rol(id_rol):
    if 'username' in session:
        rol = Rol.query.get(id_rol)
        return render_template('CRUD/rol/crud_rol.html', rol=rol)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_rol/<int:id_rol>', methods=['GET', 'POST'])
def editar_rol(id_rol):
    if 'username' in session:
        rol = Rol.query.get(id_rol)
        
        if request.method == 'POST':
            rol.nombre_rol = request.form['nombre_rol']
            
            try:
                db.session.commit()
                flash('Rol actualizado exitosamente', 'success')
                return redirect(url_for('creation.crear_rol'))
            except Exception as e:
                flash(f'Error al actualizar el rol: {str(e)}', 'error')
                db.session.rollback()

        return render_template('CRUD/rol/editar_rol.html', rol=rol)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_rol/<int:id_rol>')
def eliminar_rol(id_rol):
    if 'username' in session:
        try:
            rol = Rol.query.get(id_rol)
            if rol:
                db.session.delete(rol)
                db.session.commit()
                flash('Rol eliminado exitosamente', 'success')
            return redirect(url_for('creation.crear_rol'))
        except Exception as e:
            flash(f'Error al eliminar el rol: {str(e)}', 'error')
            db.session.rollback()
            return redirect(url_for('creation.crear_rol'))
    else:
        return redirect(url_for('auth.login'))

# ==================== CRUD ROL USUARIO ====================

@crud.route('/api/crear_rol_usuario_ajax', methods=['POST'])
def crear_rol_usuario_ajax():
    if 'username' in session:
        nombre_rol_usuario = request.form.get('nombre_rol_usuario', '').strip()
        
        if not nombre_rol_usuario:
            return jsonify({'success': False, 'message': 'El nombre del rol de usuario es requerido'}), 400
        
        try:
            nuevo_rol_usuario = RolUsuario(nombre_rol_usuario=nombre_rol_usuario)
            db.session.add(nuevo_rol_usuario)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Rol de usuario creado exitosamente',
                'rol_usuario': {
                    'id_rol_usuario': nuevo_rol_usuario.id_rol_usuario,
                    'nombre_rol_usuario': nuevo_rol_usuario.nombre_rol_usuario
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

@crud.route('/crud_rol_usuario/<int:id_rol_usuario>')
def crud_rol_usuario(id_rol_usuario):
    if 'username' in session:
        rol_usuario = RolUsuario.query.get(id_rol_usuario)
        return render_template('CRUD/rol_usuario/crud_rol_usuario.html', rol_usuario=rol_usuario)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_rol_usuario/<int:id_rol_usuario>', methods=['GET', 'POST'])
def editar_rol_usuario(id_rol_usuario):
    if 'username' in session:
        rol_usuario = RolUsuario.query.get(id_rol_usuario)
        
        if request.method == 'POST':
            rol_usuario.nombre_rol_usuario = request.form['nombre_rol_usuario']
            
            try:
                db.session.commit()
                flash('Rol de usuario actualizado exitosamente', 'success')
                return redirect(url_for('creation.crear_rol_usuario'))
            except Exception as e:
                flash(f'Error al actualizar el rol de usuario: {str(e)}', 'error')
                db.session.rollback()

        return render_template('CRUD/rol_usuario/editar_rol_usuario.html', rol_usuario=rol_usuario)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_rol_usuario/<int:id_rol_usuario>')
def eliminar_rol_usuario(id_rol_usuario):
    if 'username' in session:
        try:
            rol_usuario = RolUsuario.query.get(id_rol_usuario)
            if rol_usuario:
                db.session.delete(rol_usuario)
                db.session.commit()
                flash('Rol de usuario eliminado exitosamente', 'success')
            return redirect(url_for('creation.crear_rol_usuario'))
        except Exception as e:
            flash(f'Error al eliminar el rol de usuario: {str(e)}', 'error')
            db.session.rollback()
            return redirect(url_for('creation.crear_rol_usuario'))
    else:
        return redirect(url_for('auth.login'))

# ==================== CRUD TIPO VEHICULO ====================

@crud.route('/api/crear_tipo_vehiculo_ajax', methods=['POST'])
def crear_tipo_vehiculo_ajax():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        
        nombre_tv = request.form.get('nombre_tv', '').strip()
        
        if not nombre_tv:
            return jsonify({'success': False, 'message': 'El nombre del tipo de vehículo es requerido'}), 400
        
        try:
            nuevo_tipo_vehiculo = TipoVehiculo(nombre_tv=nombre_tv, id_dpto_empresa=departamento_usuario)
            db.session.add(nuevo_tipo_vehiculo)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Tipo de vehículo creado exitosamente',
                'tipo_vehiculo': {
                    'id_tv': nuevo_tipo_vehiculo.id_tv,
                    'nombre_tv': nuevo_tipo_vehiculo.nombre_tv
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

@crud.route('/crud_tipo_vehiculo/<int:id_tv>')
def crud_tipo_vehiculo(id_tv):
    if 'username' in session:
        tipo_vehiculo = TipoVehiculo.query.get(id_tv)
        return render_template('CRUD/tipo_vehiculo/crud_tipo_vehiculo.html', tipo_vehiculo=tipo_vehiculo)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/editar_tipo_vehiculo/<int:id_tv>', methods=['GET', 'POST'])
def editar_tipo_vehiculo(id_tv):
    if 'username' in session:
        tipo_vehiculo = TipoVehiculo.query.get(id_tv)
        
        if request.method == 'POST':
            tipo_vehiculo.nombre_tv = request.form['nombre_tv']
            
            try:
                db.session.commit()
                flash('Tipo de vehículo actualizado exitosamente', 'success')
                return redirect(url_for('creation.crear_tv'))
            except Exception as e:
                flash(f'Error al actualizar el tipo de vehículo: {str(e)}', 'error')
                db.session.rollback()

        return render_template('CRUD/tipo_vehiculo/editar_tipo_vehiculo.html', tipo_vehiculo=tipo_vehiculo)
    else:
        return redirect(url_for('auth.login'))

@crud.route('/eliminar_tipo_vehiculo/<int:id_tv>')
def eliminar_tipo_vehiculo(id_tv):
    if 'username' in session:
        try:
            tipo_vehiculo = TipoVehiculo.query.get(id_tv)
            if tipo_vehiculo:
                db.session.delete(tipo_vehiculo)
                db.session.commit()
                flash('Tipo de vehículo eliminado exitosamente', 'success')
            return redirect(url_for('creation.crear_tv'))
        except Exception as e:
            flash(f'Error al eliminar el tipo de vehículo: {str(e)}', 'error')
            db.session.rollback()
            return redirect(url_for('creation.crear_tv'))
    else:
        return redirect(url_for('auth.login'))