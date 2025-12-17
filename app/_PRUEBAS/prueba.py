# from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from shapely.geometry import Point, Polygon
# from pyproj import Proj, Transformer, CRS
# from datetime import datetime
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.exc import IntegrityError
# import pandas as pd
# import base64
# import json

# app = Flask(__name__)
# app.secret_key = '110-306-725'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/basureros'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# DATABASE_URI = 'mysql://root@localhost/basureros'
# engine = create_engine(DATABASE_URI)
# Session = sessionmaker(bind=engine)
# db = SQLAlchemy(app)

# # MODELOS
# class Area(db.Model):
#     id_area = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     nombre_area = db.Column(db.String(40), nullable=False)
#     tipo_area = db.Column(db.String(50), nullable=False)
#     coordenadas = db.relationship('Coordenadas', backref='area', cascade='all, delete')

# class Cargo(db.Model):
#     id_cargo = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     nombre_cargo = db.Column(db.String(30), nullable=False)
#     personales = db.relationship('Personal', backref='cargo', cascade='all, delete')
    
# class Falla(db.Model):
#     id_falla = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     nombre_falla = db.Column(db.String(255), nullable=False)

# class Coordenadas(db.Model):
#     id_coordenadas = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     latitud = db.Column(db.Float(precision=15, asdecimal=True), nullable=False)
#     longitud = db.Column(db.Float(precision=15, asdecimal=True), nullable=False)
#     id_area = db.Column(db.BigInteger, db.ForeignKey('area.id_area'), nullable=False)

# class DetalleFalla(db.Model):
#     id_df = db.Column(db.BigInteger, primary_key=True)
#     nombre_df = db.Column(db.String(255), nullable=False)
#     id_falla = db.Column(db.BigInteger, db.ForeignKey('falla.id_falla'), nullable=False)

# class DetalleEP(db.Model):
#     id_detalle = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     id_personal = db.Column(db.BigInteger, db.ForeignKey('personal.id_personal'), nullable=False)
#     id_programacion = db.Column(db.BigInteger, db.ForeignKey('programacion.id_programacion'), nullable=False)

# class DetalleTV(db.Model):
#     id_dtv = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     nombre_dtv = db.Column(db.String(30), nullable=False)
#     id_tv = db.Column(db.BigInteger, db.ForeignKey('tipo_vehiculo.id_tv'), nullable=False)
#     tipo_vehiculo = db.relationship('TipoVehiculo', backref='detalles')

# class DetencionesLargas(db.Model):
#     id_dl = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     fecha_hora = db.Column(db.TIMESTAMP, nullable=False)
#     descripcion = db.Column(db.String(255), nullable=False)
#     otro = db.Column(db.String(255), nullable=True)
#     id_vehiculo = db.Column(db.BigInteger, db.ForeignKey('vehiculo.id_vehiculo'), nullable=False)
#     id_falla = db.Column(db.BigInteger, db.ForeignKey('falla.id_falla'), nullable=True)

# class EquipoPersonal(db.Model):
#     id_ep = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     nombre_ep = db.Column(db.String(30), nullable=False)
#     fecha_hora = db.Column(db.TIMESTAMP, nullable=False)
#     id_personal = db.Column(db.BigInteger, db.ForeignKey('personal.id_personal'), nullable=False)
#     personal = db.relationship('Personal', backref='equipos', uselist=True)

# class Personal(db.Model):
#     id_personal = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     rut_personal = db.Column(db.String(12), nullable=False)
#     nombre_personal = db.Column(db.String(30), nullable=False)
#     apellido_paterno = db.Column(db.String(30), nullable=False)
#     apellido_materno = db.Column(db.String(30), nullable=False)
#     fecha_contrato = db.Column(db.DATE, nullable=False)
#     fono = db.Column(db.BigInteger, nullable=False)
#     estado = db.Column(db.String(20), nullable=False)
#     id_cargo = db.Column(db.BigInteger, db.ForeignKey('cargo.id_cargo'), nullable=False)

# class Parametro(db.Model):
#     id_parametro = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     nombre_parametro = db.Column(db.String(50), nullable=False)
#     segundos_parametro = db.Column(db.Integer, nullable=False)
#     velocidad_parametro = db.Column(db.Integer, nullable=False)
#     distancia_parametro = db.Column(db.Numeric, nullable=False)

# class Programacion(db.Model):
#     id_programacion = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     fecha = db.Column(db.TIMESTAMP, nullable=False)
#     id_personal = db.Column(db.BigInteger, db.ForeignKey('personal.id_personal'), nullable=False)
#     id_area = db.Column(db.BigInteger, db.ForeignKey('area.id_area'), nullable=False)
#     id_turno = db.Column(db.BigInteger, db.ForeignKey('turno.id_turno'), nullable=False)
#     id_vehiculo = db.Column(db.BigInteger, db.ForeignKey('vehiculo.id_vehiculo'), nullable=False)

# class Rol(db.Model):
#     id_rol = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     nombre_rol = db.Column(db.String(30), nullable=False)

# class Romana(db.Model):
#     id_romana = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     fecha_hora = db.Column(db.TIMESTAMP, nullable=False)
#     tonelada = db.Column(db.Float, nullable=False)
#     operador_romana = db.Column(db.String(100), nullable=False)
#     id_vehiculo = db.Column(db.BigInteger, db.ForeignKey('vehiculo.id_vehiculo'), nullable=False)
#     id_turno = db.Column(db.BigInteger, db.ForeignKey('turno.id_turno'), nullable=False)

# class TipoVehiculo(db.Model):
#     __tablename__='tipo_vehiculo'
#     id_tv = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     nombre_tv = db.Column(db.String(30), nullable=False)

# class Turno(db.Model):
#     id_turno = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     nombre_turno = db.Column(db.String(30), nullable=False)
#     horario_inicio = db.Column(db.TIMESTAMP, nullable=False)
#     horario_termino = db.Column(db.TIMESTAMP, nullable=False)

# class Vehiculo(db.Model):
#     id_vehiculo = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     patente = db.Column(db.String(6), nullable=False)
#     gps = db.Column(db.String(100), nullable=False)
#     estado = db.Column(db.String(30), nullable=True)
#     foto = db.Column(db.LargeBinary, nullable=True)
#     id_tv = db.Column(db.BigInteger, db.ForeignKey('tipo_vehiculo.id_tv'), nullable=True)
#     id_dtv = db.Column(db.BigInteger, db.ForeignKey('detalle_tv.id_dtv'), nullable=True)
#     coordenadas_vehiculo = db.relationship('CoordenadasVehiculo', backref='vehiculo', cascade='all, delete')
#     tipo_vehiculo = db.relationship('TipoVehiculo', backref='vehiculos')

# class CoordenadasVehiculo(db.Model):
#     __tablename__='coordenadas_vehiculo'
#     id_coordenadas_vehiculo = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
#     latitud = db.Column(db.Numeric(precision=15, scale=14), nullable=False)
#     longitud = db.Column(db.Numeric(precision=15, scale=14), nullable=False)
#     fecha = db.Column(db.DATE, nullable=False)
#     hora = db.Column(db.TIME, nullable=False)
#     id_vehiculo = db.Column(db.BigInteger, db.ForeignKey('vehiculo.id_vehiculo'), nullable=False)

# opcion_coor = 1

# if opcion_coor == 1:
#     crs_actual = CRS.from_epsg(4326)
# else:
#     crs_actual = CRS.from_epsg(32719)

# crs_nuevo = CRS.from_epsg(32719)
# transformador = Transformer.from_crs(crs_actual, crs_nuevo, always_xy=True)

# # INDEX
# @app.route('/', methods=['GET', 'POST'])
# def index():
#     global opcion_coor

#     if request.method == 'POST':
#         opcion_coor = int(request.form['opcion_coor'])
#         if opcion_coor == 1:
#             crs_actual = CRS.from_epsg(4326)
#         else:
#             crs_actual = CRS.from_epsg(32719)

#         transformador = Transformer.from_crs(crs_actual, crs_nuevo, always_xy=True)

#     return render_template('index.html', opcion_coor=opcion_coor)

# # FUNCIONES CARGO
# @app.route('/crear_cargo', methods=['GET', 'POST'])
# def crear_cargo():
#     if request.method == 'POST':
#         nombre_cargo = request.form['nombre_cargo']
#         nuevo_cargo = Cargo(nombre_cargo=nombre_cargo)

#         db.session.add(nuevo_cargo)
#         db.session.commit()

#         return redirect(url_for('crear_cargo'))

#     return render_template('datos/crear_cargo.html')

# # FUNCIONES ROL
# @app.route('/crear_rol', methods=['GET', 'POST'])
# def crear_rol():
#     if request.method == 'POST':
#         nombre_rol = request.form['nombre_rol']
#         nuevo_rol = Rol(nombre_rol=nombre_rol)

#         db.session.add(nuevo_rol)
#         db.session.commit()

#         return redirect(url_for('crear_rol'))

#     return render_template('datos/crear_rol.html')

# # FUNCIONES TURNO
# @app.route('/crear_turno', methods=['GET', 'POST'])
# def crear_turno():
#     if request.method == 'POST':
#         nombre_turno = request.form['nombre_turno']
#         horario_inicio = request.form['horario_inicio']
#         horario_termino = request.form['horario_termino']
#         nuevo_turno = Turno(
#             nombre_turno=nombre_turno,
#             horario_inicio=horario_inicio,
#             horario_termino=horario_termino)

#         db.session.add(nuevo_turno)
#         db.session.commit()

#         return redirect(url_for('crear_turno'))

#     return render_template('datos/crear_turno.html')

# # FUNCIONES PROGRAMACION
# @app.route('/crear_programacion', methods=['GET', 'POST'])
# def crear_programacion():
#     if request.method == 'POST':
#         fecha_hora_str = request.form['fecha_programacion']
#         id_personal = request.form['nombre_personal']
#         id_area = request.form['nombre_area']
#         id_turno = request.form['turno']
#         id_vehiculo = request.form['vehiculo']

#         fecha_hora = datetime.strptime(fecha_hora_str, '%Y-%m-%dT%H:%M')

#         nueva_programacion = Programacion(
#             fecha=fecha_hora,
#             id_personal=id_personal,
#             id_area=id_area,
#             id_turno=id_turno,
#             id_vehiculo=id_vehiculo
#         )

#         db.session.add(nueva_programacion)
#         db.session.commit()

#         return redirect(url_for('crear_programacion'))

#     supervisores_activos = Personal.query.join(Cargo).filter(Cargo.nombre_cargo == 'Supervisor', Personal.estado == 'Activo').all()
#     areas = Area.query.filter_by(tipo_area='z_trabajos').all()
#     turnos = Turno.query.all()
#     vehiculos = Vehiculo.query.filter_by(estado='Activo').all()

#     return render_template('datos/crear_programacion.html', personal=supervisores_activos, areas=areas, turnos=turnos, vehiculos=vehiculos)

# # FUNCIONES

# # FUNCIONES COORDENADAS
# def guardar_areas_trabajo(tipo_area, areas_trabajo):
#     with app.app_context():
#         for numero, area in areas_trabajo.items():
#             nueva_area = Area(nombre_area=area['nombre'], tipo_area=tipo_area)
#             db.session.add(nueva_area)

#         try:
#             db.session.commit()
#         except Exception as e:
#             print(f"Error al intentar realizar la commit: {e}")
#             db.session.rollback()

# def ingresar_area_trabajo(tipo_area, areas_trabajo, nombre_area, coordenadas, id_area):
#     coordenadas_numeros = [[float(coord[0]), float(coord[1])] for coord in json.loads(coordenadas)]
#     coordenadas_utm = [transformador.transform(coord[1], coord[0]) for coord in coordenadas_numeros]

#     with app.app_context():
#         nueva_area = Area(nombre_area=str(nombre_area), tipo_area=tipo_area)
#         db.session.add(nueva_area)

#         try:
#             db.session.commit()
#         except Exception as e:
#             print(f"Error al intentar realizar la commit: {e}")
#             db.session.rollback()

#         id_area = nueva_area.id_area

#         for coord_utm in coordenadas_utm:
#             nueva_coordenada = Coordenadas(
#                 latitud=json.dumps(coord_utm[1]),
#                 longitud=json.dumps(coord_utm[0]),
#                 id_area=id_area
#             )
#             db.session.add(nueva_coordenada)

#         try:
#             db.session.commit()
#         except Exception as e:
#             print(f"Error al intentar realizar la commit: {e}")
#             db.session.rollback()

#         print(f"{tipo_area.capitalize()} '{nombre_area}' guardado con éxito.")

# @app.route('/menu_coordenadas', methods=['GET', 'POST'])
# def menu_coordenadas():
#     return render_template('menu/menu_coordenadas.html')

# @app.route('/ingresar_coordenadas', methods=['GET', 'POST'])
# def ingresar_area_trabajo_route():
#     global opcion_coor

#     if request.method == 'POST':
#         nombre_area = request.form['nombre_area']
#         coordenadas = request.form['coordenadas']
#         tipo_area = request.form['tipo_area']
#         id_area = request.form['id_area']

#         if tipo_area == 'cuadrantes':
#             areas_trabajo = 'cuadrantes'
#         elif tipo_area == 'sectores':
#             areas_trabajo = 'sectores'
#         elif tipo_area == 'z_trabajos':
#             areas_trabajo = 'z_trabajos'
#         elif tipo_area == 'cercos':
#             areas_trabajo = 'cercos'

#         ingresar_area_trabajo(tipo_area, areas_trabajo, nombre_area, coordenadas, id_area)
#         return redirect(url_for('ingresar_area_trabajo_route'))

#     return render_template('datos/crear_coordenadas.html', opcion_coor=opcion_coor)

# @app.route('/carga_masiva_coordenadas', methods=['GET', 'POST'])
# def carga_masiva_coordenadas():
#     if request.method == 'POST':
#         archivo_excel = request.files['archivo_excel']

#         if archivo_excel and archivo_excel.filename.endswith(('.xlsx', '.xls')):
#             df = pd.read_excel(archivo_excel)

#             df = df.dropna(subset=['NombreArea'])

#             session = Session()

#             try:
#                 for index, row in df.iterrows():
#                     area_existente = session.query(Area).filter_by(nombre_area=row['NombreArea']).first()

#                     if area_existente:
#                         area_existente.nombre_area = row['NombreArea']
#                         nueva_area = area_existente
#                     else:
#                         nueva_area = Area(
#                             nombre_area=row['NombreArea'],
#                             tipo_area=row['TipoArea'],
#                         )
#                         session.add(nueva_area)

#                     longitud, latitud = transformador.transform(row['Longitud'], row['Latitud'])
#                     nueva_coordenada = Coordenadas(
#                         latitud=latitud,
#                         longitud=longitud,
#                         area=nueva_area
#                     )
#                     session.add(nueva_coordenada)

#                 session.commit()

#                 return redirect(url_for('index'))
#             except IntegrityError as e:
#                 print(f"Error de integridad: {e}")
#                 session.rollback()
#             except Exception as e:
#                 print(f"Error al intentar realizar la commit: {e}")
#                 session.rollback()
#             finally:
#                 session.close()

#     return render_template('cargas/carga_masiva_coordenadas.html') 

# @app.route('/crud_coordenadas', methods=['GET', 'POST'])
# def crud_coordenadas():
#     global opcion_coor

#     if request.method == 'POST':
#         tipo_area = request.form['tipo_area']

#         if tipo_area == 'cuadrantes':
#             areas = Area.query.filter_by(tipo_area='cuadrantes').all()
#         elif tipo_area == 'sectores':
#             areas = Area.query.filter_by(tipo_area='sectores').all()
#         elif tipo_area == 'z_trabajos':
#             areas = Area.query.filter_by(tipo_area='z_trabajos').all()
#         elif tipo_area == 'cercos':
#             areas = Area.query.filter_by(tipo_area='cercos').all()
#         else:
#             areas = None

#         if 'nombre_area' in request.form and 'nuevas_coordenadas' in request.form:

#             nombre_area = request.form['nombre_area']
#             nuevas_coordenadas = request.form['nuevas_coordenadas']

#             if nuevas_coordenadas:
#                 area = Area.query.filter_by(nombre_area=nombre_area).first()

#                 if area:
#                     id_area = area.id_area

#                     print(f"Eliminando coordenadas existentes para el área con ID {id_area}")
#                     Coordenadas.query.filter_by(id_area=id_area).delete()

#                     coordenadas_lat_lon = [[float(coord[0]), float(coord[1])] for coord in json.loads(nuevas_coordenadas)]
#                     coordenadas_utm = [transformador.transform(coord[1], coord[0]) for coord in coordenadas_lat_lon]

#                     for coord_utm in coordenadas_utm:
#                         nueva_coordenada = Coordenadas(latitud=coord_utm[1], longitud=coord_utm[0], area=area)
#                         db.session.add(nueva_coordenada)

#                     try:
#                         db.session.commit()
#                         print(f"Coordenadas para el área con ID {id_area} actualizadas con éxito.")
#                     except Exception as e:
#                         print(f"Error al intentar realizar la commit: {e}")
#                         db.session.rollback()

#                     return redirect(url_for('crud_coordenadas'))

#         return render_template('CRUD/coordenadas/crud_coordenadas.html', tipo_area=tipo_area, areas=areas)

#     return render_template('CRUD/coordenadas/crud_coordenadas.html', tipo_area=None, areas=None)

# def obtener_coordenadas_desde_db(id_area):
#     with app.app_context():
#         coordenadas_db = Coordenadas.query.filter_by(id_area=id_area).all()
#         coordenadas = [(coord.latitud, coord.longitud) for coord in coordenadas_db]
#         return json.dumps(coordenadas)

# # FUNCIONES VEHICULO
# @app.route('/detalles_tv/<int:tipo_vehiculo_id>')
# def detalles_tv(tipo_vehiculo_id):
#     detalles_tv = DetalleTV.query.filter_by(id_tv=tipo_vehiculo_id).all()
#     detalles_tv_data = [{'id_dtv': detalle.id_dtv, 'nombre_dtv': detalle.nombre_dtv} for detalle in detalles_tv]
#     return jsonify(detalles_tv_data)

# @app.route('/menu_vehiculo', methods=['GET', 'POST'])
# def menu_vehiculo():
#     return render_template('menu/menu_vehiculo.html')

# @app.route('/crear_vehiculo', methods=['GET', 'POST'])
# def crear_vehiculo():
#     if request.method == 'POST':
#         patente = request.form['patente']
#         gps = request.form['gps']
#         estado = request.form['estado']
#         tipo_vehiculo = request.form['tipo_vehiculo']
#         detalle_tv = request.form['detalles_tv']
        
#         if 'foto' in request.files:
#             foto = request.files['foto'].read()
#         else:
#             foto = None

#         nuevo_vehiculo = Vehiculo(
#             patente=patente,
#             gps=gps,
#             estado=estado,
#             foto=foto,
#             id_tv=tipo_vehiculo,
#             id_dtv = detalle_tv
#         )

#         db.session.add(nuevo_vehiculo)
#         db.session.commit()

#         return redirect(url_for('lista_vehiculo'))
#     tipo_vehiculo = TipoVehiculo.query.all()

#     return render_template('datos/crear_vehiculo.html', tipo_vehiculo=tipo_vehiculo)

# @app.route('/seleccionar_vehiculo', methods=['GET', 'POST'])
# def seleccionar_vehiculo():
#     if request.method == 'POST':
#         id_vehiculo = request.form['id_vehiculo']

#         coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo).order_by(CoordenadasVehiculo.fecha, CoordenadasVehiculo.hora).all()
#         vehiculo = Vehiculo.query.get(id_vehiculo)

#         tiempo_anterior = None
#         areas = Area.query.all()
#         parametros = Parametro.query.all()  # Obtener todos los parámetros

#         informe_data = []

#         for i in range(len(coordenadas_vehiculo)):
#             distancia, tiempo_transcurrido = calcular_distancia_tiempo(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i], tiempo_anterior) if i > 0 else (0, 0)

#             tipos_de_area, nombres_de_area = coordenada_pertenece_a_areas(coordenadas_vehiculo[i], areas)

#             velocidad = 0 if tiempo_transcurrido == 0 else distancia / tiempo_transcurrido
#             velocidad_kilometros = velocidad * 3.6

#             for parametro in parametros:
#                 if tiempo_transcurrido > parametro.segundos_parametro:
                    
#                     estado = parametro.nombre_parametro
#                     break
#                 elif distancia == 0:
#                     estado = 'Inicio' 
#                 else:
#                     estado = 'Activo'

#             informe_data.append({
#                 'patente': vehiculo.patente,
#                 'fecha': coordenadas_vehiculo[i].fecha,
#                 'hora': coordenadas_vehiculo[i].hora,
#                 'latitud': coordenadas_vehiculo[i].latitud,
#                 'longitud': coordenadas_vehiculo[i].longitud,
#                 'distancia': distancia,
#                 'velocidad': velocidad_kilometros,
#                 'tiempo': tiempo_transcurrido,
#                 'estado': estado,
#                 'tipos_area': tipos_de_area,
#                 'nombres_area': nombres_de_area
#             })

#             tiempo_anterior = datetime.strptime(f"{coordenadas_vehiculo[i].fecha} {coordenadas_vehiculo[i].hora}", "%Y-%m-%d %H:%M:%S")

#         return render_template('informe.html', informe_data=informe_data, vehiculo=vehiculo)

#     vehiculos = Vehiculo.query.all()

#     return render_template('seleccionar_vehiculo.html', vehiculos=vehiculos)

# def calcular_distancia_tiempo(coord_1, coord_2, tiempo_anterior):
#     # Convierte las coordenadas de Decimal a float
#     latitud_1, longitud_1 = float(coord_1.latitud), float(coord_1.longitud)
#     latitud_2, longitud_2 = float(coord_2.latitud), float(coord_2.longitud)

#     distancia = ((latitud_2 - latitud_1)**2 + (longitud_2 - longitud_1)**2)**0.5

#     fecha_hora_actual = datetime.strptime(f"{coord_2.fecha} {coord_2.hora}", "%Y-%m-%d %H:%M:%S")
#     fecha_hora_anterior = datetime.strptime(f"{coord_1.fecha} {coord_1.hora}", "%Y-%m-%d %H:%M:%S")
#     tiempo_transcurrido = (fecha_hora_actual - fecha_hora_anterior).total_seconds()

#     return distancia, tiempo_transcurrido

# def coordenada_pertenece_a_areas(coordenada, areas):
#     punto = Point(float(coordenada.latitud), float(coordenada.longitud))
#     tipos_de_area = []
#     nombres_de_area = []

#     for area in areas:
#         coordenadas_area = [(float(coord.latitud), float(coord.longitud)) for coord in area.coordenadas]
#         poligono_area = Polygon(coordenadas_area)

#         if punto.within(poligono_area):
#             tipos_de_area.append(area.tipo_area)
#             nombres_de_area.append(area.nombre_area)

#     return (tipos_de_area, nombres_de_area) if tipos_de_area else ([], [])

# @app.route('/descargar_informe_excel', methods=['POST'])
# def descargar_informe_excel():
#     id_vehiculo = request.form['id_vehiculo']

#     # Obtener las coordenadas, fecha, hora y patente del vehículo seleccionado
#     coordenadas_vehiculo = CoordenadasVehiculo.query.filter_by(id_vehiculo=id_vehiculo).order_by(CoordenadasVehiculo.fecha, CoordenadasVehiculo.hora).all()
#     vehiculo = Vehiculo.query.get(id_vehiculo)

#     tiempo_anterior = None
#     areas = Area.query.all()
#     parametros = Parametro.query.all()

#     informe_data = []

#     for i in range(len(coordenadas_vehiculo)):
#         distancia, tiempo_transcurrido = calcular_distancia_tiempo(coordenadas_vehiculo[i-1], coordenadas_vehiculo[i], tiempo_anterior) if i > 0 else (0, 0)

#         tipos_de_area, nombres_de_area = coordenada_pertenece_a_areas(coordenadas_vehiculo[i], areas)

#         velocidad = 0 if tiempo_transcurrido == 0 else distancia / tiempo_transcurrido
#         velocidad_kilometros = velocidad * 3.6

#         for parametro in parametros:
#             if tiempo_transcurrido > parametro.segundos_parametro:
#                 estado = parametro.nombre_parametro
#                 break
#             elif distancia == 0:
#                 estado = 'Inicio' 
#             else:
#                 estado = 'Activo'

#         informe_data.append({
#             'Patente': vehiculo.patente,
#             'GPS': vehiculo.gps,
#             'Tipo Vehiculo': vehiculo.tipo_vehiculo,
#             'Estado': estado,
#             'Fecha': coordenadas_vehiculo[i].fecha,
#             'Hora': coordenadas_vehiculo[i].hora,
#             'Latitud(UTMY)': coordenadas_vehiculo[i].latitud,
#             'Longitud(UTMX)': coordenadas_vehiculo[i].longitud,
#             'Distancia (M)': distancia,
#             'Velocidad (km/h)': velocidad_kilometros,
#             'Tiempo (s)': tiempo_transcurrido,
#             'Tipos Área': tipos_de_area,
#             'Nombres área': nombres_de_area
#         })

#         tiempo_anterior = datetime.strptime(f"{coordenadas_vehiculo[i].fecha} {coordenadas_vehiculo[i].hora}", "%Y-%m-%d %H:%M:%S")
#     # Convertir los datos del informe en un DataFrame de Pandas
#     df = pd.DataFrame(informe_data)

#     # Nombre del archivo Excel con la patente del vehículo
#     excel_filename = f'informe_vehiculo_{vehiculo.patente}.xlsx'

#     # Guardar el DataFrame como un archivo Excel
#     df.to_excel(excel_filename, index=False)

#     # Devolver el archivo Excel como una descarga
#     return send_file(excel_filename, as_attachment=True)

# @app.route('/crud_vehiculo/<int:id_vehiculo>')
# def crud_vehiculo(id_vehiculo):
#     vehiculo = Vehiculo.query.get(id_vehiculo)

#     if vehiculo:
#         return render_template('CRUD/vehiculo/crud_vehiculo.html', vehiculo=vehiculo)

#     return render_template('ERROR/error.html', mensaje='Vehículo no encontrado')

# @app.route('/editar_vehiculo/<int:id_vehiculo>', methods=['GET', 'POST'])
# def editar_vehiculo(id_vehiculo):
#     vehiculo = Vehiculo.query.get(id_vehiculo)
#     tipos_vehiculo = TipoVehiculo.query.all()

#     if request.method == 'POST':
#         vehiculo.patente = request.form['patente']
#         vehiculo.gps = request.form['gps']
#         vehiculo.estado = request.form['estado']
#         vehiculo.id_tv = request.form['tipo_vehiculo']
#         vehiculo.id_dtv = request.form['detalles_tv']

#         if 'foto' in request.files:
#             nueva_foto = request.files['foto']
#             if nueva_foto.filename != '':
#                 vehiculo.foto = nueva_foto.read()

#         db.session.commit()
#         return redirect(url_for('lista_vehiculo'))

#     return render_template('CRUD/vehiculo/editar_vehiculo.html', vehiculo=vehiculo, tipo_vehiculo=tipos_vehiculo)

# @app.route('/eliminar_vehiculo/<int:id_vehiculo>')
# def eliminar_vehiculo(id_vehiculo):
#     vehiculo = Vehiculo.query.get(id_vehiculo)

#     if vehiculo:
#         db.session.delete(vehiculo)
#         db.session.commit()

#     return redirect(url_for('lista_vehiculo'))

# @app.route('/carga_masiva_vehiculo', methods=['GET', 'POST'])
# def carga_masiva_vehiculo():
#     if request.method == 'POST':
#         archivo_excel = request.files['archivo_excel']

#         if archivo_excel and archivo_excel.filename.endswith(('.xlsx', '.xls')):
#             # Lee el archivo Excel y carga los datos en un DataFrame de Pandas
#             df = pd.read_excel(archivo_excel)

#             # Elimina filas con al menos un valor nulo en la columna 'IMEI'
#             df = df.dropna(subset=['IMEI'])

#             # Crea una nueva sesión
#             session = Session()

#             try:
#                 # Itera sobre las filas del DataFrame y guarda en la base de datos
#                 for index, row in df.iterrows():
#                     # Verifica si el IMEI ya existe en la base de datos
#                     vehiculo_existente = session.query(Vehiculo).filter_by(gps=row['IMEI']).first()

#                     if vehiculo_existente:
#                         # Si existe, actualiza la fila existente
#                         vehiculo_existente.patente = row['Vehiculo']
#                         nuevo_vehiculo = vehiculo_existente
#                     else:
#                         # Si no existe, crea un nuevo vehículo
#                         nuevo_vehiculo = Vehiculo(
#                             patente=row['Vehiculo'],
#                             gps=row['IMEI'],
#                         )
#                         session.add(nuevo_vehiculo)

#                     # Formatea la fecha y la hora antes de la inserción
#                     fecha_obj = datetime.strptime(row['Fecha'], '%d-%m-%Y')
#                     fecha_formateada = fecha_obj.strftime('%Y-%m-%d')
#                     longitud, latitud = transformador.transform(row['Longitud'], row['Latitud'])

#                     nueva_coordenada_vehiculo = CoordenadasVehiculo(
#                         latitud=latitud,
#                         longitud=longitud,
#                         fecha=fecha_formateada,
#                         hora=row['Hora'],
#                         vehiculo=nuevo_vehiculo
#                     )
#                     session.add(nueva_coordenada_vehiculo)

#                 session.commit()

#                 return redirect(url_for('menu_vehiculo'))
#             except IntegrityError as e:
#                 print(f"Error de integridad: {e}")
#                 session.rollback()
#             except Exception as e:
#                 # En caso de otros errores, realiza un rollback
#                 print(f"Error al intentar realizar la commit: {e}")
#                 session.rollback()
#             finally:
#                 # Cierra la sesión
#                 session.close()

#     return render_template('cargas/carga_masiva_vehiculo.html')

# @app.route('/lista_vehiculo')
# def lista_vehiculo():
#     lista_vehiculo = Vehiculo.query.all()

#     for vehiculo in lista_vehiculo:
#         if vehiculo.foto:
#             vehiculo.foto_encoded = base64.b64encode(vehiculo.foto).decode('utf-8')
#         else:
#             vehiculo.foto_encoded = None

#     return render_template('listas/lista_vehiculo.html', vehiculo=lista_vehiculo)

# # FUNCIONES PERSONAL
# @app.route('/menu_personal', methods=['GET', 'POST'])
# def menu_personal():
#     return render_template('menu/menu_personal.html')

# @app.route('/crud_personal/<int:id_personal>')
# def crud_personal(id_personal):
#     personal = Personal.query.get(id_personal)

#     if personal:
#         return render_template('CRUD/personal/crud_personal.html', personal=personal)

#     return render_template('ERROR/error.html', mensaje='Personal no encontrado')

# @app.route('/crear_personal', methods=['GET', 'POST'])
# def crear_personal():
#     if request.method == 'POST':
#         rut_personal = request.form['rut_personal']
#         nombre_personal = request.form['nombre_personal']
#         apellido_paterno = request.form['apellido_paterno']
#         apellido_materno = request.form['apellido_materno']
#         fecha_contrato = request.form['fecha_contrato']
#         fono = request.form['fono']
#         estado = request.form['estado']
#         id_cargo = request.form['id_cargo']

#         nuevo_personal = Personal(
#             rut_personal=rut_personal,
#             nombre_personal=nombre_personal,
#             apellido_paterno=apellido_paterno,
#             apellido_materno=apellido_materno,
#             fecha_contrato=fecha_contrato,
#             fono=fono,
#             estado=estado,
#             id_cargo=id_cargo
#         )

#         db.session.add(nuevo_personal)

#         try:
#             db.session.commit()
#             print(f"Personal '{nombre_personal}' agregado con éxito.")
#             return redirect(url_for('menu_personal'))
#         except Exception as e:
#             print(f"Error al intentar realizar la commit: {e}")
#             db.session.rollback()

#     cargos = Cargo.query.all()

#     return render_template('datos/crear_personal.html', cargos=cargos)

# @app.route('/editar_personal/<int:id_personal>', methods=['GET', 'POST'])
# def editar_personal(id_personal):
#     personal = Personal.query.get(id_personal)

#     if request.method == 'POST':
#         personal.rut_personal = request.form['rut_personal']
#         personal.nombre_personal = request.form['nombre_personal']
#         personal.apellido_paterno = request.form['apellido_paterno']
#         personal.apellido_materno = request.form['apellido_materno']
#         personal.fecha_contrato = request.form['fecha_contrato']
#         personal.fono = request.form['fono']
#         personal.estado = request.form['estado']
#         personal.id_cargo = request.form['id_cargo']

#         db.session.commit()
#         return redirect(url_for('lista_personal'))

#     cargos = Cargo.query.all()

#     return render_template('CRUD/personal/editar_personal.html', personal=personal, cargos=cargos)

# @app.route('/eliminar_personal/<int:id_personal>')
# def eliminar_personal(id_personal):
#     personal = Personal.query.get(id_personal)

#     if personal:
#         db.session.delete(personal)
#         db.session.commit()

#     return redirect(url_for('lista_personal'))

# @app.route('/lista_personal')
# def lista_personal():
#     lista_personal = Personal.query.all()

#     return render_template('listas/lista_personal.html', personal=lista_personal)

# # FUNCIONES EQUIPO PERSONAL
# @app.route('/menu_equipo', methods=['GET', 'POST'])
# def menu_equipo():
#     return render_template('menu/menu_equipo.html')

# @app.route('/crear_equipo', methods=['GET', 'POST'])
# def crear_equipo():
#     if request.method == 'POST':
#         nombre_equipo = request.form['nombre_equipo']
#         fecha_hora_str = request.form['fecha_hora']
#         id_personal_list = request.form.getlist('id_personal')

#         print(f"Nombre: {nombre_equipo}")
#         print(f"Fecha y Hora: {fecha_hora_str}")
#         print(f"ID Personal List: {id_personal_list}")

#         fecha_hora = datetime.strptime(fecha_hora_str, '%Y-%m-%dT%H:%M')

#         nuevo_equipo = EquipoPersonal(
#             nombre_ep=nombre_equipo,
#             fecha_hora=fecha_hora
#         )

#         for id_persona in id_personal_list:
#             personal = Personal.query.filter_by(id_personal=id_persona, estado='Activo').first()
#             if personal:
#                 nuevo_equipo = EquipoPersonal(
#                     nombre_ep=nombre_equipo,
#                     fecha_hora=fecha_hora,
#                     id_personal=id_persona
#                 )
#                 db.session.add(nuevo_equipo)

#         db.session.commit()

#         return redirect(url_for('menu_equipo'))

#     personal_activos = Personal.query.filter_by(estado='Activo').all()

#     return render_template('datos/crear_equipo.html', personal=personal_activos)

# @app.route('/crud_equipo/<int:id_ep>')
# def crud_equipo(id_ep):
#     equipo = EquipoPersonal.query.get(id_ep)

#     if equipo:
#         return render_template('CRUD/equipo_personal/crud_equipo.html', equipo=equipo)

#     return render_template('ERROR/error.html', mensaje='Equipo no encontrado')

# @app.route('/editar_equipo/<int:id_ep>', methods=['GET', 'POST'])
# def editar_equipo(id_ep):
#     equipo = EquipoPersonal.query.get(id_ep)

#     if request.method == 'POST':
#         nombre_equipo = request.form['nombre_equipo']
#         fecha_hora_str = request.form['fecha_hora']
#         id_personal_list = request.form.getlist('id_personal')

#         fecha_hora = datetime.strptime(fecha_hora_str, '%Y-%m-%dT%H:%M')

#         equipo.nombre_ep = nombre_equipo
#         equipo.fecha_hora = fecha_hora
#         equipo.integrantes = []  # Limpiar los integrantes actuales

#         for id_persona in id_personal_list:
#             personal = Personal.query.filter_by(id_personal=id_persona, estado='Activo').first()
#             if personal:
#                 equipo.integrantes.append(personal)

#         db.session.commit()

#         return redirect(url_for('lista_equipos'))

#     personal_activos = Personal.query.filter_by(estado='Activo').all()

#     return render_template('CRUD/equipo_personal/editar_equipo.html', equipo=equipo, personal=personal_activos)

# @app.route('/eliminar_equipo/<int:id_ep>')
# def eliminar_equipo(id_ep):
#     equipo = EquipoPersonal.query.get(id_ep)

#     if equipo:
#         db.session.delete(equipo)
#         db.session.commit()

#     return redirect(url_for('lista_equipos'))

# @app.route('/lista_equipos', methods=['GET'])
# def lista_equipos():
#     equipos = EquipoPersonal.query.all()
#     personal = Personal.query.all()

#     equipos_con_integrantes = []
#     for equipo in equipos:
#         integrantes = Personal.query.filter_by(id_personal=equipo.id_personal).all()
#         equipos_con_integrantes.append({'equipo': equipo, 'integrantes': integrantes})

#     return render_template('listas/lista_equipos.html', equipos_con_integrantes=equipos_con_integrantes, personal=personal)

# # FUNCIONES PARAMETROS
# @app.route('/crear_parametro', methods=['GET', 'POST'])
# def crear_parametro():
#     if request.method == 'POST':
#         nombre_parametro = request.form['nombre_parametro']
#         segundos_parametro = int(request.form['segundos_parametro']) * 60
#         distancia_parametro = int(request.form['distancia_parametro'])
#         velocidad_parametro = float(request.form['velocidad_parametro']) * 3.6


#         nuevo_parametro = Parametro(nombre_parametro=nombre_parametro, segundos_parametro=segundos_parametro, distancia_parametro=distancia_parametro, velocidad_parametro=velocidad_parametro)

#         db.session.add(nuevo_parametro)
#         db.session.commit()

#         return redirect(url_for('crear_parametro'))
#     return render_template('datos/crear_parametro.html')

# @app.route('/crud_parametro/<int:id_parametro>')
# def crud_parametro(id_parametro):
#     parametro = Parametro.query.get(id_parametro)

#     if parametro:
#         return render_template('CRUD/parametro/crud_parametro.html', parametro=parametro)

#     return render_template('ERROR/error.html', mensaje='Parametro no encontrado')

# @app.route('/editar_parametro/<int:id_parametro>', methods=['GET', 'POST'])
# def editar_parametro(id_parametro):
#     parametro = Parametro.query.get(id_parametro)

#     if request.method == 'POST':
#         parametro.nombre_parametro = request.form['nombre_parametro']
#         parametro.segundos_parametro = int(request.form['segundos_parametro']) * 60

#         db.session.commit()
#         return redirect(url_for('lista_parametros'))

#     return render_template('CRUD/parametro/editar_parametro.html', parametro=parametro)

# @app.route('/eliminar_parametro/<int:id_parametro>')
# def eliminar_parametro(id_parametro):
#     parametro = Parametro.query.get(id_parametro)

#     if parametro:
#         db.session.delete(parametro)
#         db.session.commit()

#     return redirect(url_for('lista_parametros'))

# @app.route('/lista_parametros')
# def lista_parametros():
#     lista_parametros = Parametro.query.all()
#     return render_template('listas/lista_parametros.html', parametro=lista_parametros)

# # FUNCIONES TIPO VEHICULO
# @app.route('/crear_tipo_vehiculo', methods=['GET', 'POST'])
# def crear_tv():
#     if request.method == 'POST':
#         nombre_tv = request.form['nombre_tv']
#         nuevo_tv = TipoVehiculo(nombre_tv=nombre_tv)

#         db.session.add(nuevo_tv)
#         db.session.commit()

#         return redirect(url_for('lista_tv'))

#     return render_template('datos/crear_tipo_vehiculo.html')

# @app.route('/crud_tipo_vehiculo/<int:id_tv>')
# def crud_tv(id_tv):
#     tv = TipoVehiculo.query.get(id_tv)

#     if tv:
#         return render_template('CRUD/tipo_vehiculo/crud_tipo_vehiculo.html', tv=tv)

#     return render_template('ERROR/error.html', mensaje='Tipo no encontrado')

# @app.route('/editar_tipo_vehiculo/<int:id_tv>', methods=['GET', 'POST'])
# def editar_tv(id_tv):
#     tv = TipoVehiculo.query.get(id_tv)

#     if request.method == 'POST':
#         tv.nombre_tv = request.form['nombre_tv']

#         db.session.commit()
#         return redirect(url_for('lista_tv'))

#     return render_template('CRUD/tipo_vehiculo/editar_tipo_vehiculo.html', tv=tv)

# @app.route('/eliminar_tipo_vehiculo/<int:id_tv>')
# def eliminar_tv(id_tv):
#     tv = TipoVehiculo.query.get(id_tv)

#     if tv:
#         db.session.delete(tv)
#         db.session.commit()

#     return redirect(url_for('lista_tv'))

# @app.route('/lista_tipo_vehiculos')
# def lista_tv():
#     lista_tv = TipoVehiculo.query.all()

#     return render_template('listas/lista_tipo_vehiculo.html', tv=lista_tv)

# # FUNCIONES DETALLE TIPO VEHICULO
# @app.route('/crear_detalle', methods=['GET', 'POST'])
# def crear_detalle():
#     if request.method == 'POST':
#         tipo_vehiculo_id = request.form['tipo_vehiculo']
#         nombre_dtv = request.form['nombre_dtv']

#         # Crea un nuevo detalle de tipo de vehículo
#         nuevo_detalle_tv = DetalleTV(nombre_dtv=nombre_dtv, id_tv=tipo_vehiculo_id)

#         # Guarda en la base de datos
#         db.session.add(nuevo_detalle_tv)
#         db.session.commit()

#     tipo_vehiculo = TipoVehiculo.query.all()  # Obtén todos los tipos de vehículo desde la base de datos
#     return render_template('datos/crear_detalle.html', tipo_vehiculo=tipo_vehiculo)

# @app.route('/lista_detalle_vehiculo')
# def lista_dtv():
#     lista_dtv = DetalleTV.query.all()
#     return render_template('listas/lista_detalle_vehiculo.html', dtv=lista_dtv)

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)