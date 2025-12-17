from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from pyproj import Proj, Transformer, CRS, transform
from math import radians, sin, cos, sqrt, atan2
from shapely.geometry import Point, Polygon
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from collections import defaultdict
from datetime import datetime
from sqlalchemy import or_
from time import sleep
import pandas as pd
import requests
import base64
import json

app = Flask(__name__)
app.secret_key = '110-306-725'
DATABASE_URI = 'mysql://root@localhost/fleet_manager'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
db = SQLAlchemy(app)

# MODELOS
class Area(db.Model):
    __tablename__='area'
    id_area = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_area = db.Column(db.String(40), nullable=False)
    tipo_area = db.Column(db.String(50), nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)
    coordenadas = db.relationship('Coordenadas', backref='area', cascade='all, delete')

class Cargo(db.Model):
    id_cargo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_cargo = db.Column(db.String(30), nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)
    dpto_empresa = db.relationship('DptoEmpresa', backref='cargo')

class Coordenadas(db.Model):
    id_coordenadas = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    latitud = db.Column(db.Float(precision=19, asdecimal=True), nullable=False)
    longitud = db.Column(db.Float(precision=19, asdecimal=True), nullable=False)
    grados_latitud = db.Column(db.Float(precision=19, asdecimal=True), nullable=False)
    grados_longitud = db.Column(db.Float(precision=19, asdecimal=True), nullable=False)
    id_area = db.Column(db.Integer, db.ForeignKey('area.id_area'), nullable=False)

class CoordenadasVehiculo(db.Model):
    __tablename__='coordenadas_vehiculo'
    id_coordenadas_vehiculo = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    latitud = db.Column(db.Numeric(precision=19, scale=12), nullable=False)
    longitud = db.Column(db.Numeric(precision=19, scale=12), nullable=False)
    grados_latitud = db.Column(db.Numeric(precision=19, scale=12), nullable=False)
    grados_longitud = db.Column(db.Numeric(precision=19, scale=12), nullable=False)
    fecha = db.Column(db.DATE, nullable=False)
    hora = db.Column(db.TIME, nullable=False)
    estado = db.Column(db.SMALLINT, nullable=True)
    distancia_r = db.Column(db.Integer, nullable=True)
    distancia_m = db.Column(db.Integer, nullable=True)
    id_vehiculo = db.Column(db.Integer, db.ForeignKey('vehiculo.id_vehiculo'), nullable=False)

class DetalleEP(db.Model):
    id_detalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_personal = db.Column(db.Integer, db.ForeignKey('personal.id_personal'), nullable=False)
    id_rol = db.Column(db.Integer, db.ForeignKey('rol.id_rol'), nullable=False)
    id_programacion = db.Column(db.Integer, db.ForeignKey('programacion.id_programacion'), nullable=False)

class DetalleFalla(db.Model):
    id_df = db.Column(db.Integer, primary_key=True)
    nombre_df = db.Column(db.String(255), nullable=False)
    id_falla = db.Column(db.Integer, db.ForeignKey('falla.id_falla'), nullable=False)

class DetalleTV(db.Model):
    id_dtv = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_dtv = db.Column(db.String(30), nullable=False)
    id_tv = db.Column(db.Integer, db.ForeignKey('tipo_vehiculo.id_tv'), nullable=False)

class DetencionesLargas(db.Model):
    __tablename__='detenciones_largas'
    id_dl = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha_hora = db.Column(db.TIMESTAMP, nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    otro = db.Column(db.String(255), nullable=True)
    id_vehiculo = db.Column(db.Integer, db.ForeignKey('vehiculo.id_vehiculo'), nullable=False)
    id_falla = db.Column(db.Integer, db.ForeignKey('falla.id_falla'), nullable=True)

class DptoEmpresa(db.Model):
    __tablename__='dpto_empresa'
    id_dpto_empresa = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_dpto_empresa = db.Column(db.String(30), nullable=False)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id_empresa'), nullable=False)
    empresa = db.relationship('Empresa', backref='dpto_empresa')
    tipo_vehiculo = db.relationship('TipoVehiculo', backref='dpto_empresa')

class Empresa(db.Model):
    id_empresa = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_empresa = db.Column(db.String(30), nullable=False)

class Equipo(db.Model):
    id_equipo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_equipo = db.Column(db.String(30), nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)

class EquipoPersonal(db.Model):
    id_ep = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_equipo = db.Column(db.Integer, db.ForeignKey('equipo.id_equipo'), nullable=False)
    id_personal = db.Column(db.Integer, db.ForeignKey('personal.id_personal'), nullable=False)
    personal = db.relationship('Personal', backref='equipos', uselist=True)
    equipo = db.relationship('Equipo', backref='equipos', uselist=True)

class Falla(db.Model):
    id_falla = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_falla = db.Column(db.String(255), nullable=False)

class Flota(db.Model):
    id_flota = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_flota = db.Column(db.String(30), nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)
    dpto_empresa = db.relationship('DptoEmpresa', backref='flota')

class Investigacion(db.Model):
    id_folio_investigacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    feha_investigacion = db.Column(db.TIMESTAMP, nullable=False)
    descripcion_investigacion = db.Column(db.String(255), nullable=False)
    condicion = db.Column(db.String(10), nullable=False)
    danio = db.Column(db.String(10), nullable=False)
    foto = db.Column(db.LargeBinary, nullable=True)
    resolucion = db.Column(db.String(255), nullable=False)
    id_dl = db.Column(db.Integer, db.ForeignKey('detenciones_largas.id_dl'))
    id_personal_responsable = db.Column(db.Integer, db.ForeignKey('personal.id_personal'))
    id_personal_investigador = db.Column(db.Integer, db.ForeignKey('personal.id_personal'))
    id_cargo_investigador = db.Column(db.Integer, db.ForeignKey('cargo.id_cargo'))

class Pagina(db.Model):
    id_pagina = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_pagina = db.Column(db.String(100), nullable=True)

class Parametro(db.Model):
    id_parametro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_parametro = db.Column(db.String(50), nullable=False)
    segundos_parametro = db.Column(db.Integer, nullable=False)
    velocidad_parametro = db.Column(db.Integer, nullable=False)
    distancia_parametro = db.Column(db.Numeric, nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)

class PermisoDptoUsuario:
    __tablename__='permiso_dpto_usuario'
    id_pdu = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)

class PermisoPagina:
    id_permiso_pagina = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(db.String(10), nullable=False)
    id_rol_usuario = db.Column(db.Integer, db.ForeignKey('rol_usuario.id_rol_usuario'))
    id_pagina = db.Column(db.Integer, db.ForeignKey('pagina.id_pagina'))

class Personal(db.Model):
    id_personal = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rut_personal = db.Column(db.String(12), nullable=False)
    nombre_personal = db.Column(db.String(20), nullable=False)
    apellido_paterno = db.Column(db.String(30), nullable=False)
    apellido_materno = db.Column(db.String(30), nullable=False)
    fecha_contrato = db.Column(db.DATE, nullable=False)
    fono = db.Column(db.String(12), nullable=False)
    estado = db.Column(db.String(20), nullable=False)
    id_cargo = db.Column(db.Integer, db.ForeignKey('cargo.id_cargo'), nullable=False)
    cargo = db.relationship('Cargo', backref='personal')

class Programacion(db.Model):
    id_programacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha = db.Column(db.DATE, nullable=False)
    id_personal = db.Column(db.Integer, db.ForeignKey('personal.id_personal'), nullable=False)
    id_area = db.Column(db.Integer, db.ForeignKey('area.id_area'), nullable=False)
    id_turno = db.Column(db.Integer, db.ForeignKey('turno.id_turno'), nullable=False)
    id_vehiculo = db.Column(db.Integer, db.ForeignKey('vehiculo.id_vehiculo'), nullable=False)

class Rol(db.Model):
    id_rol = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_rol = db.Column(db.String(30), nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)

class RolUsuario(db.Model):
    __tablename__='rol_usuario'
    id_rol_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_rol_usuario = db.Column(db.String(30), nullable=False)

class Romana(db.Model):
    id_romana = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha_hora = db.Column(db.TIMESTAMP, nullable=False)
    toneladas = db.Column(db.Float, nullable=False)
    operador_romana = db.Column(db.String(100), nullable=False)
    id_vehiculo = db.Column(db.Integer, db.ForeignKey('vehiculo.id_vehiculo'), nullable=False)
    id_turno = db.Column(db.Integer, db.ForeignKey('turno.id_turno'), nullable=False)

class TipoVehiculo(db.Model):
    __tablename__='tipo_vehiculo'
    id_tv = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_tv = db.Column(db.String(30), nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)
    detalle_tv = db.relationship('DetalleTV', backref='tipo_vehiculo')

class Turno(db.Model):
    id_turno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_turno = db.Column(db.String(30), nullable=False)
    horario_inicio = db.Column(db.TIME, nullable=False)
    horario_termino = db.Column(db.TIME, nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)

class Usuario(db.Model):
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(12), nullable=False)
    password = db.Column(db.String(162), nullable=False)
    id_personal = db.Column(db.Integer, db.ForeignKey('personal.id_personal'), nullable=True)
    id_rol_usuario = db.Column(db.Integer, db.ForeignKey('rol_usuario.id_rol_usuario'), nullable=True)
    personal = db.relationship('Personal', backref='usuario')

class Vehiculo(db.Model):
    id_vehiculo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patente = db.Column(db.String(12), nullable=False)
    gps = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(15), nullable=True)
    foto = db.Column(db.LargeBinary, nullable=True)
    restriccion = db.Column(db.SMALLINT, nullable=True)
    id_dtv = db.Column(db.Integer, db.ForeignKey('detalle_tv.id_dtv'), nullable=True)
    id_flota = db.Column(db.Integer, db.ForeignKey('flota.id_flota'), nullable=True)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'))
    coordenadas_vehiculo = db.relationship('CoordenadasVehiculo', backref='vehiculo')
    flota = db.relationship('Flota', backref='vehiculos')
    detalle_tv = db.relationship('DetalleTV', backref='vehiculos')

crs_actual = CRS.from_epsg(4326)
crs_nuevo = CRS.from_epsg(32719)
transformador = Transformer.from_crs(crs_actual, crs_nuevo, always_xy=True)

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

        # Obtener los integrantes del equipo seleccionado
        id_equipo_seleccionado = request.args.get('equipo')
        integrantes_equipo = EquipoPersonal.query.filter_by(id_equipo=id_equipo_seleccionado).all()

        return render_template('datos/crear_programacion.html', equipos=equipos, personales=personal_equipo, personal=supervisores_activos, areas=areas, turnos=turnos, vehiculos=vehiculos, roles=roles, integrantes_equipo=integrantes_equipo)
    else:
        return redirect(url_for('login'))

# FUNCIONES AREAS
def guardar_areas_trabajo(tipo_area, areas_trabajo):
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
            flash('Área eliminada exitosamente.', 'success')
            return redirect(url_for('lista_areas'))
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
                flash('Área actualizada exitosamente.', 'success')
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

            usuario_existente = Usuario.query.filter_by(username=username).first()
            if usuario_existente:
                flash('El nombre de usuario ya está en uso. Por favor, elija otro.')
                return redirect(url_for('crear_usuario'))

            password_encriptada = generate_password_hash(password_plano)

            nuevo_usuario = Usuario(username=username, 
                                    password=password_encriptada,
                                    id_rol_usuario=rol_usuario,
                                    id_personal=id_personal)
            db.session.add(nuevo_usuario)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Error al registrar el usuario. Por favor, inténtelo de nuevo.')
                return redirect(url_for('crear_usuario'))

            return redirect(url_for('login'))
        
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

        # Obtener solo los vehículos del mismo departamento de empresa que el usuario logueado
        vehiculos = Vehiculo.query.filter_by(id_dpto_empresa=departamento_usuario).all()

        return render_template('seleccionar_vehiculo.html', vehiculos=vehiculos)
    else:
        return redirect(url_for('login'))

@app.route('/informe_vehiculo/<int:id_vehiculo>', methods=['GET', 'POST'])
def informe_vehiculo(id_vehiculo):
    if 'username' in session:
        vehiculo = Vehiculo.query.get(id_vehiculo)
        
        if vehiculo:
            if request.method == 'POST':
                fecha_seleccionada = request.form['fecha']
                if fecha_seleccionada == 'mostrarTodo':
                    coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo).order_by(CoordenadasVehiculo.fecha, CoordenadasVehiculo.hora).all()
                else:
                    coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo, fecha=fecha_seleccionada).order_by(CoordenadasVehiculo.fecha, CoordenadasVehiculo.hora).all()
            else:
                fecha_seleccionada = datetime.now().date()  # Si no se envía una fecha, se toma la fecha actual
                coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo, fecha=fecha_seleccionada).order_by(CoordenadasVehiculo.hora).all()

            informe_data = []
            fechas_disponibles = reversed(sorted(set(coord.fecha.strftime('%Y-%m-%d') for coord in CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo).all())))
            fecha_anterior = None
            tiempo_anterior = None
            areas = Area.query.filter(Area.id_dpto_empresa == vehiculo.id_dpto_empresa).all()
            parametros = Parametro.query.filter(Parametro.id_dpto_empresa == vehiculo.id_dpto_empresa).all()

            delta_latitud_anterior = 0
            delta_longitud_anterior = 0
            pendiente_anterior = 0

            for i in range(len(coordenadas_vehiculo)):
                distancia = calcular_distancia(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i]) if i > 0 else (0, 0)
                tiempo_transcurrido = calcular_tiempo(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i]) if i > 0 else (0, 0)
                pendiente, delta_latitud, delta_longitud = calcular_pendiente(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i])
                tipos_de_area, nombres_de_area = coordenada_pertenece_a_areas(coordenadas_vehiculo[i], areas)

                velocidad = 0 if tiempo_transcurrido == 0 else distancia / tiempo_transcurrido
                velocidad_kilometros = velocidad * 3.6

                if not distancia:
                    continue

                if not delta_latitud or not delta_longitud:
                    pass

                caso_actual_1 = delta_latitud < 0 and delta_longitud > 0 and pendiente < 0
                caso_actual_2 = delta_latitud > 0 and delta_longitud < 0 and pendiente < 0
                caso_actual_3 = delta_latitud > 0 and delta_longitud > 0 and pendiente > 0
                caso_actual_4 = delta_latitud < 0 and delta_longitud < 0 and pendiente > 0

                caso_antiguo_1 = delta_latitud_anterior < 0 and delta_longitud_anterior > 0 and pendiente_anterior < 0 
                caso_antiguo_2 = delta_latitud_anterior > 0 and delta_longitud_anterior < 0 and pendiente_anterior < 0
                caso_antiguo_3 = delta_latitud_anterior > 0 and delta_longitud_anterior > 0 and pendiente_anterior > 0
                caso_antiguo_4 = delta_latitud_anterior < 0 and delta_longitud_anterior < 0 and pendiente_anterior > 0

                if (((caso_actual_1 and caso_antiguo_2) == True) or ((caso_actual_2 and caso_antiguo_1) == True) or ((caso_actual_3 and caso_antiguo_4) == True) or ((caso_actual_4 and caso_antiguo_3) == True)):
                    # Ignorar la coordenada actual
                    coordenadas_vehiculo[i].estado = 2 # Coordenada no válida
                    db.session.commit()
                    continue

                if velocidad_kilometros >= 120:
                    # Ignorar la coordenada actual
                    coordenadas_vehiculo[i].estado = 2 # Coordenada no válida
                    db.session.commit()
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
                    'fecha': coordenadas_vehiculo[i].fecha,
                    'hora': coordenadas_vehiculo[i].hora,
                    'latitud': coordenadas_vehiculo[i].latitud,
                    'longitud': coordenadas_vehiculo[i].longitud,
                    'distancia': round(distancia),
                    'velocidad': round(velocidad_kilometros, 1),
                    'tiempo': tiempo_transcurrido,
                    'estado': estado,
                    'tipos_area': tipos_de_area,
                    'nombres_area': nombres_de_area
                })

                fecha_anterior = coordenadas_vehiculo[i].fecha  # Actualizar la fecha anterior
                tiempo_anterior = datetime.strptime(f"{coordenadas_vehiculo[i].fecha} {coordenadas_vehiculo[i].hora}", "%Y-%m-%d %H:%M:%S")
                delta_latitud_anterior = delta_latitud
                delta_longitud_anterior = delta_longitud
                pendiente_anterior = pendiente

            return render_template('informe.html', informe_data=informe_data, vehiculo=vehiculo, fecha_seleccionada=fecha_seleccionada, fechas_disponibles=fechas_disponibles)
        else:
            return render_template('error.html', mensaje='El vehículo seleccionado no existe.')
    else:
        return redirect(url_for('login'))

@app.route('/descargar_informe_excel', methods=['POST'])
def descargar_informe_excel():
    if 'username' in session:
        id_vehiculo = request.form['id_vehiculo']

        # Obtener las coordenadas, fecha, hora y patente del vehículo seleccionado
        coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo).order_by(CoordenadasVehiculo.fecha, CoordenadasVehiculo.hora).all()
        vehiculo = Vehiculo.query.get(id_vehiculo)

        fecha_anterior = None
        tiempo_anterior = None
        areas = Area.query.filter(Area.id_dpto_empresa == vehiculo.id_dpto_empresa).all()
        parametros = Parametro.query.filter(Parametro.id_dpto_empresa == vehiculo.id_dpto_empresa).all()
        informe_data = []
        delta_latitud_anterior = 0
        delta_longitud_anterior = 0
        pendiente_anterior = 0

        for i in range(len(coordenadas_vehiculo)):
            distancia = calcular_distancia(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i]) if i > 0 else (0, 0)
            tiempo_transcurrido = calcular_tiempo(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i]) if i > 0 else (0, 0)

            tipos_de_area, nombres_de_area = coordenada_pertenece_a_areas(coordenadas_vehiculo[i], areas)
            pendiente, delta_latitud, delta_longitud = calcular_pendiente(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i])

            velocidad = 0 if tiempo_transcurrido == 0 else distancia / tiempo_transcurrido
            velocidad_kilometros = velocidad * 3.6

            if not distancia:
                    continue

            if not delta_latitud or not delta_longitud:
                pass

            caso_actual_1 = delta_latitud < 0 and delta_longitud > 0 and pendiente < 0
            caso_actual_2 = delta_latitud > 0 and delta_longitud < 0 and pendiente < 0
            caso_actual_3 = delta_latitud > 0 and delta_longitud > 0 and pendiente > 0
            caso_actual_4 = delta_latitud < 0 and delta_longitud < 0 and pendiente > 0

            caso_antiguo_1 = delta_latitud_anterior < 0 and delta_longitud_anterior > 0 and pendiente_anterior < 0 
            caso_antiguo_2 = delta_latitud_anterior > 0 and delta_longitud_anterior < 0 and pendiente_anterior < 0
            caso_antiguo_3 = delta_latitud_anterior > 0 and delta_longitud_anterior > 0 and pendiente_anterior > 0
            caso_antiguo_4 = delta_latitud_anterior < 0 and delta_longitud_anterior < 0 and pendiente_anterior > 0

            if (((caso_actual_1 and caso_antiguo_2) == True) or ((caso_actual_2 and caso_antiguo_1) == True) or ((caso_actual_3 and caso_antiguo_4) == True) or ((caso_actual_4 and caso_antiguo_3) == True)):
                continue

            if velocidad_kilometros >= 120:
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
                'Fecha': coordenadas_vehiculo[i].fecha,
                'Hora': coordenadas_vehiculo[i].hora,
                'Latitud': coordenadas_vehiculo[i].latitud,
                'Longitud': coordenadas_vehiculo[i].longitud,
                'Distancia (m)': distancia,
                'Velocidad (Km/h)': round(velocidad_kilometros),
                'Tiempo (s)': round(tiempo_transcurrido),
                'Estado': estado,
                'Tipos Área': tipos_de_area,
                'Nombres Área': nombres_de_area
            })

            fecha_anterior = coordenadas_vehiculo[i].fecha  # Actualizar la fecha anterior
            tiempo_anterior = datetime.strptime(f"{coordenadas_vehiculo[i].fecha} {coordenadas_vehiculo[i].hora}", "%Y-%m-%d %H:%M:%S")
            delta_latitud_anterior = delta_latitud
            delta_longitud_anterior = delta_longitud
            pendiente_anterior = pendiente
        # Convertir los datos del informe en un DataFrame de Pandas
        df = pd.DataFrame(informe_data)

        # Nombre del archivo Excel con la patente del vehículo
        excel_filename = f'informe_vehiculo_{vehiculo.patente}.xlsx'

        # Guardar el DataFrame como un archivo Excel
        df.to_excel(excel_filename, index=False)

        # Devolver el archivo Excel como una descarga
        return send_file(excel_filename, as_attachment=True)
    else:
        return redirect(url_for('login'))

@app.route('/ver_trayecto/<int:id_vehiculo>')
def ver_trayecto(id_vehiculo):
    if 'username' in session:
        vehiculo = Vehiculo.query.get(id_vehiculo)
        coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo, estado=1).order_by(CoordenadasVehiculo.fecha.desc(), CoordenadasVehiculo.hora).all()
        fechas_disponibles = list(reversed(sorted(set(coord.fecha.strftime('%Y-%m-%d') for coord in coordenadas_vehiculo))))
        
        coordenadas_json = []
        delta_latitud_anterior = 0
        delta_longitud_anterior = 0
        pendiente_anterior = 0
        fecha_anterior = None

        for i, coord in enumerate(coordenadas_vehiculo):
            j = i + 1
            while j < len(coordenadas_vehiculo) and coordenadas_vehiculo[j].estado != 2:
                coord_siguiente_valida = coordenadas_vehiculo[j]

                distancia = calcular_distancia(coord, coord_siguiente_valida)
                tiempo_transcurrido = calcular_tiempo(coord, coord_siguiente_valida)
                pendiente, delta_latitud, delta_longitud = calcular_pendiente(coord, coord_siguiente_valida)

                if not distancia:
                    break

                velocidad = 0 if tiempo_transcurrido == 0 else distancia / tiempo_transcurrido
                velocidad_kilometros = velocidad * 3.6

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
                    coordenadas_vehiculo[j].estado = 2 # Coordenada no válida - SALTOS ELIMINAR PUNTO SIGUIENTE
                    db.session.commit()
                    j += 1
                    continue # Ignora

                if velocidad_kilometros >= 120:
                    coordenadas_vehiculo[j].estado = 2 # Coordenada no válida
                    db.session.commit()
                    j += 1
                    continue # Ignora

                delta_latitud_anterior = delta_latitud
                delta_longitud_anterior = delta_longitud
                pendiente_anterior = pendiente

                if fecha_anterior != coordenadas_vehiculo[j].fecha:
                    # Si es la primera coordenada de una nueva fecha, establecer distancia en 0
                    coordenadas_json.append({
                        'latitud': coordenadas_vehiculo[j].grados_latitud,
                        'longitud': coordenadas_vehiculo[j].grados_longitud,
                        'fecha': coordenadas_vehiculo[j].fecha.strftime('%Y-%m-%d'),
                        'hora': coordenadas_vehiculo[j].hora.strftime('%H:%M:%S'),
                        'velocidad': round(velocidad_kilometros) if velocidad_kilometros is not None else None,
                        'distancia': 0,
                        'pendiente': round(pendiente, 10) if pendiente is not None else None,
                        'delta_latitud': round(delta_latitud, 10) if delta_latitud is not None else None,
                        'delta_longitud': round(delta_longitud, 10) if delta_longitud is not None else None,
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
                        'pendiente': round(pendiente, 10) if pendiente is not None else None,
                        'delta_latitud': round(delta_latitud, 10) if delta_latitud is not None else None,
                        'delta_longitud': round(delta_longitud, 10) if delta_longitud is not None else None,
                        'estado': coordenadas_vehiculo[j].estado
                    })

                fecha_anterior = coordenadas_vehiculo[j].fecha
                break # Punto de quiebre

        return render_template('ver_trayecto.html', vehiculo=vehiculo, coordenadas_vehiculo=coordenadas_json, fechas_disponibles=fechas_disponibles)
    else:
        return redirect(url_for('login'))

def calcular_pendiente(coord_anterior, coord_actual):
    # Convierte a float si es necesario
    latitud_anterior = float(coord_anterior.latitud)
    longitud_anterior = float(coord_anterior.longitud)
    latitud_actual = float(coord_actual.latitud)
    longitud_actual = float(coord_actual.longitud)
    
    delta_latitud = latitud_actual - latitud_anterior
    delta_longitud = longitud_actual - longitud_anterior
    
    if delta_longitud == 0:
        pendiente = float('inf')  # Representa una pendiente indefinida/infinita
    else:
        pendiente = delta_latitud / delta_longitud

    return pendiente, delta_longitud, delta_latitud

def calcular_tiempo(coord_1, coord_2):
    fecha_hora_actual = datetime.strptime(f"{coord_2.fecha} {coord_2.hora}", "%Y-%m-%d %H:%M:%S")
    fecha_hora_anterior = datetime.strptime(f"{coord_1.fecha} {coord_1.hora}", "%Y-%m-%d %H:%M:%S")
    tiempo_transcurrido = (fecha_hora_actual - fecha_hora_anterior).total_seconds()

    return tiempo_transcurrido

def coordenada_pertenece_a_areas(coordenada, areas):
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
                df = pd.read_excel(archivo_excel)

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

# Definir la función para obtener la distancia de una ruta
def obtener_distancia_ruta(url, max_retries=2):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data['routes'][0].get('distance', 0)
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
    return 0

@app.route('/carga_masiva_coordenadas_vehiculo', methods=['GET', 'POST'])
def carga_masiva_coordenadas_vehiculo():
    if 'username' in session:
        if request.method == 'POST':
            archivo_excel = request.files['archivo_excel']

            if archivo_excel and archivo_excel.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(archivo_excel)
                df = df.dropna(subset=['Longitud', 'Latitud'])

                try:
                    coordenadas_vehiculo = []
                    for index, row in df.iterrows():
                        vehiculo = db.session.query(Vehiculo).filter_by(gps=row['IMEI']).first()

                        if vehiculo:
                            if isinstance(row['Fecha'], str):
                                fecha_obj = datetime.strptime(row['Fecha'], '%d-%m-%Y')
                            elif isinstance(row['Fecha'], pd.Timestamp):
                                fecha_obj = row['Fecha'].to_pydatetime()
                            else:
                                raise ValueError("Formato de fecha no reconocido")

                            fecha_formateada = fecha_obj.strftime('%Y-%m-%d')
                            longitud, latitud = float(row['Longitud']), float(row['Latitud'])

                            # Convertir las coordenadas a UTM
                            utm_longitud, utm_latitud = transformador.transform(longitud, latitud)

                            existing_coordinate = CoordenadasVehiculo.query.filter_by(
                                id_vehiculo=vehiculo.id_vehiculo,
                                fecha=fecha_formateada,
                                hora=row['Hora']
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

                    # Procesar las coordenadas para obtener las distancias
                    IP = "192.168.243.111"
                    PORT = "8080"
                    
                    for i in range(len(coordenadas_vehiculo)):
                        coord_curr = coordenadas_vehiculo[i]

                        if i == 0 or (i > 0 and coordenadas_vehiculo[i - 1].fecha != coord_curr.fecha):
                            distancia_r = 0
                            distancia_m = 0
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

                            distancia_r1 = distancia_r2 = distancia_r3 = 0

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
                                if distancia_r1 >= distancia_r2:
                                    coord_subnext.estado = 2
                                if distancia_r2 >= distancia_r3:
                                    coord_subnext2.estado = 2

                            print(f"r1: {distancia_r1}, r2: {distancia_r2}, r3: {distancia_r3}")
                            print(i)

                        coord_curr.distancia_r = distancia_r
                        coord_curr.distancia_m = distancia_m

                        if int(distancia_r) > int(distancia_m) + 2:
                            coord_curr.estado = 2  # Coordenada no válida

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
        return render_template('cargas/carga_masiva_coord_vehiculo.html')
    else:
        return redirect(url_for('login'))
    
def calcular_distancia(coord_1, coord_2):
    # Radio de la Tierra en kilómetros
    R = 6371000 #6371.0 

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

            # Verificar si el rut ya existe en la base de datos
            if Personal.query.filter_by(rut_personal=rut_personal).first():
                flash('El rut ingresado ya existe en la base de datos. Por favor, ingrese un rut válido.', 'error')
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
        # Recuperar todas las asociaciones de equipo_personal asociadas con el personal a eliminar
        asociaciones_equipo_personal = EquipoPersonal.query.filter_by(id_personal=id_personal).all()

        # Eliminar las asociaciones de equipo_personal
        for asociacion in asociaciones_equipo_personal:
            db.session.delete(asociacion)
        
        # Eliminar el registro de Personal
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
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)