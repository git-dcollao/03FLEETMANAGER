from app.db import db 

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
    tipo_area = db.Column(db.String(50), nullable=True)
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
    tipo_vehiculo = db.relationship('TipoVehiculo', backref='dpto_empresa')
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id_empresa'), nullable=False)
    
    empresa = db.relationship('Empresa', backref='dpto_empresa')

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

class Parametro(db.Model):
    id_parametro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_parametro = db.Column(db.String(50), nullable=False)
    segundos_parametro = db.Column(db.Integer, nullable=False)
    velocidad_parametro = db.Column(db.Integer, nullable=False)
    distancia_parametro = db.Column(db.Numeric, nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)

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
    staff = db.Column(db.SMALLINT, nullable=False)
    id_personal = db.Column(db.Integer, db.ForeignKey('personal.id_personal'), nullable=True)
    id_rol_usuario = db.Column(db.Integer, db.ForeignKey('rol_usuario.id_rol_usuario'), nullable=True)
    personal = db.relationship('Personal', backref='usuario')

class Vehiculo(db.Model):
    id_vehiculo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patente = db.Column(db.String(12), nullable=False)
    id_gps = db.Column(db.Integer, nullable=True)
    gps = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(15), nullable=True)
    foto = db.Column(db.LargeBinary, nullable=True)
    restriccion = db.Column(db.SMALLINT, nullable=True)
    id_dtv = db.Column(db.Integer, db.ForeignKey('detalle_tv.id_dtv'), nullable=True)
    id_flota = db.Column(db.Integer, db.ForeignKey('flota.id_flota'), nullable=True)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'))
    flota = db.relationship('Flota', backref='vehiculos')
    detalle_tv = db.relationship('DetalleTV', backref='vehiculos')
    coordenadas_vehiculo = db.relationship('CoordenadasVehiculo', backref='vehiculo')

class ApiConfig(db.Model):
    """Configuración de APIs de proveedores GPS"""
    __tablename__='api_config'
    id_api = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_proveedor = db.Column(db.String(50), nullable=False)  # ej: "LINKSUR", "COSEMAR"
    tipo_api = db.Column(db.String(20), nullable=False)  # "vehiculos" o "coordenadas"
    url = db.Column(db.String(500), nullable=False)
    auth_type = db.Column(db.String(20), nullable=False)  # "token", "api_key", "bearer"
    auth_value = db.Column(db.String(200), nullable=False)  # Token o API Key
    header_name = db.Column(db.String(100), nullable=True)  # Nombre del header si aplica
    activo = db.Column(db.Boolean, default=True, nullable=False)
    id_dpto_empresa = db.Column(db.Integer, db.ForeignKey('dpto_empresa.id_dpto_empresa'), nullable=False)
    intervalo_segundos = db.Column(db.Integer, default=10, nullable=False)  # Frecuencia de actualización
    descripcion = db.Column(db.String(255), nullable=True)
    fecha_creacion = db.Column(db.TIMESTAMP, server_default=db.func.now())
    fecha_actualizacion = db.Column(db.TIMESTAMP, server_default=db.func.now(), onupdate=db.func.now())
    
    dpto_empresa = db.relationship('DptoEmpresa', backref='apis')