# 🔌 Módulo de Gestión de APIs

## Descripción

Este módulo permite administrar las configuraciones de APIs de proveedores GPS de manera dinámica, sin necesidad de modificar código fuente.

## 📁 Archivos Creados

- **`app/models.py`** - Modelo `ApiConfig` agregado
- **`app/routes/api_config.py`** - Blueprint con rutas CRUD
- **`app/templates/api_config/`** - Templates HTML:
  - `listar_apis.html` - Lista todas las APIs
  - `crear_api.html` - Formulario de creación
  - `editar_api.html` - Formulario de edición
- **`init_api_config.sql`** - Script SQL con datos iniciales

## 🚀 Cómo Usar

### 1. Acceder al Módulo

1. Iniciar sesión en Fleet Manager
2. Ir a **Administración de Datos**
3. Click en **🔌 Configurar APIs**

### 2. Agregar Nueva API

1. Click en "➕ Nueva API"
2. Completar el formulario:

#### Campos Obligatorios:

- **Nombre del Proveedor**: Identificador único (ej: LINKSUR, COSEMAR, GPS ACME)
- **Tipo de API**: 
  - `vehiculos` - Para obtener lista de vehículos
  - `coordenadas` - Para obtener coordenadas GPS
- **URL**: Endpoint de la API
  - Para tokens en URL usar: `{token}` como placeholder
  - Ejemplo: `https://api.com/posicion/{token}`
- **Tipo de Autenticación**:
  - `token` - Token directamente en la URL
  - `api_key` - API Key en header HTTP
  - `bearer` - Bearer Token en header
- **Token/API Key**: Valor de autenticación
- **Departamento**: A qué departamento pertenecen estos datos
- **Intervalo (segundos)**: Frecuencia de consulta (por defecto: 10)

#### Campos Opcionales:

- **Nombre del Header**: Solo si tipo es `api_key`
- **Descripción**: Notas sobre esta API

3. Activar/desactivar checkbox "Activar API inmediatamente"
4. Click en "💾 Guardar Configuración"

### 3. Probar Conexión

Desde la lista de APIs, click en el botón **🔍** para probar la conexión:
- ✓ Verde: Conexión exitosa
- ✗ Rojo: Error de conexión

### 4. Activar/Desactivar APIs

- Click en **⏸** para pausar una API activa
- Click en **▶** para activar una API inactiva

Solo las APIs **activas** serán consultadas por los trabajos programados.

### 5. Editar Configuración

1. Click en **✏️** en la API que quieres modificar
2. Actualizar los campos necesarios
3. Guardar cambios

### 6. Eliminar API

1. Click en **🗑️** en la API que quieres eliminar
2. Confirmar la eliminación

## 🔧 Configuración Técnica

### Tipos de Autenticación Soportados

#### 1. Token en URL
```
URL: https://api.example.com/vehiculos/{token}
auth_type: token
auth_value: abc123xyz
```
El sistema reemplazará `{token}` con `abc123xyz`

#### 2. API Key en Header
```
URL: https://api.example.com/v1/vehiculos
auth_type: api_key
auth_value: my-secret-key-123
header_name: Authorization-api-key
```
Enviará header: `Authorization-api-key: my-secret-key-123`

#### 3. Bearer Token
```
URL: https://api.example.com/api/vehiculos
auth_type: bearer
auth_value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
Enviará header: `Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

## 📊 Base de Datos

### Tabla `api_config`

```sql
CREATE TABLE api_config (
    id_api INT PRIMARY KEY AUTO_INCREMENT,
    nombre_proveedor VARCHAR(50) NOT NULL,
    tipo_api VARCHAR(20) NOT NULL,  -- 'vehiculos' o 'coordenadas'
    url VARCHAR(500) NOT NULL,
    auth_type VARCHAR(20) NOT NULL,  -- 'token', 'api_key', 'bearer'
    auth_value VARCHAR(200) NOT NULL,
    header_name VARCHAR(100),
    activo BOOLEAN DEFAULT TRUE,
    id_dpto_empresa INT NOT NULL,
    intervalo_segundos INT DEFAULT 10,
    descripcion VARCHAR(255),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_dpto_empresa) REFERENCES dpto_empresa(id_dpto_empresa)
);
```

### Inicializar Datos de Ejemplo

```bash
# Conectar a MySQL
docker exec -it fleet_manager_db mysql -u root -pcontra123 fleet_manager

# Ejecutar script
mysql> source /path/to/init_api_config.sql;
```

O desde fuera del contenedor:
```bash
docker exec -i fleet_manager_db mysql -u root -pcontra123 fleet_manager < init_api_config.sql
```

## 🔄 Integración con Código Existente

### Funciones Modificadas en `api.py`

Las siguientes funciones ahora leen configuraciones desde la BD:

- `obtener_vehiculos_linksur(app)`
- `obtener_coordenadas_linksur(app)`
- `obtener_vehiculos_cosemar(app)`
- `obtener_coordenadas_cosemar(app)` (parcial)

### Funciones Auxiliares Nuevas

```python
def get_api_config(nombre_proveedor, tipo_api):
    """Obtiene configuración activa de una API"""
    return ApiConfig.query.filter_by(
        nombre_proveedor=nombre_proveedor,
        tipo_api=tipo_api,
        activo=True
    ).first()

def make_api_request(api_config):
    """Ejecuta petición HTTP usando configuración"""
    # Maneja autenticación automáticamente
    # Retorna JSON o None en caso de error
```

## 📝 Ejemplos de Uso

### Ejemplo 1: LINKSUR (SmartGPS)

```
Nombre: LINKSUR
Tipo: vehiculos
URL: https://smartgps.gpsserver.xyz/v3/apis/global_api/v3.0.0/public/index.php/obtener_posicion_actual/{token}
Auth Type: token
Token: e0a9528e7a5f181568f797e7f2d7c355
Departamento: Aseo (id: 7)
Intervalo: 5 segundos
```

### Ejemplo 2: COSEMAR (InducomGPS)

```
Nombre: COSEMAR
Tipo: vehiculos
URL: https://api.inducomgps.com/v1/vehiculos?fields[]=patente
Auth Type: api_key
API Key: 71c627fc-8987-46b9-93f8-4d257a2a26fc
Header: Authorization-api-key
Departamento: Aseo (id: 7)
Intervalo: 5 segundos
```

### Ejemplo 3: Nuevo Proveedor GPS

```
Nombre: GPS_TRACKING_PRO
Tipo: coordenadas
URL: https://api.gpstracking.com/v2/positions
Auth Type: bearer
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkw...
Departamento: Transporte (id: 8)
Intervalo: 15 segundos
```

## ⚠️ Consideraciones Importantes

### Seguridad

- ✅ Tokens/API Keys almacenados en BD (no en código)
- ⚠️ **Recomendación**: Encriptar `auth_value` en producción
- ⚠️ Considerar usar variables de entorno para credenciales sensibles

### Rendimiento

- El intervalo mínimo recomendado es **5 segundos**
- Intervalos muy cortos pueden causar rate limiting en APIs externas
- Desactivar APIs no utilizadas para optimizar recursos

### APScheduler

Las funciones programadas en `app/__init__.py` están comentadas por defecto:

```python
# Descomentar para activar sincronización automática
scheduler.add_job(
    func=lambda: obtener_vehiculos_linksur(app), 
    trigger=IntervalTrigger(seconds=5), 
    id='job_datos', 
    replace_existing=True
)
```

Ahora usan las configuraciones dinámicas de la BD.

## 🐛 Troubleshooting

### Error: "No hay configuración activa"

**Solución**: Verificar que existe una API con:
- Nombre del proveedor correcto
- Tipo de API correcto
- Campo `activo = TRUE`

### Error de conexión en Test

1. Verificar URL está correcta
2. Comprobar que token/API key es válido
3. Revisar tipo de autenticación
4. Verificar conectividad de red

### Las coordenadas no se actualizan

1. Verificar que la API esté **activa**
2. Revisar logs: `docker-compose logs -f app`
3. Comprobar que los jobs están descomentados en `__init__.py`
4. Verificar intervalo de actualización

## 📚 Próximas Mejoras

- [ ] Encriptación de tokens en BD
- [ ] Historial de peticiones API
- [ ] Estadísticas de uso por API
- [ ] Notificaciones de errores
- [ ] Soporte para POST/PUT requests
- [ ] Variables de entorno para tokens
- [ ] Logs de auditoría

## 🤝 Contribución

Para agregar soporte a un nuevo proveedor GPS:

1. Crear configuración en la interfaz web
2. Si la API tiene formato diferente, adaptar las funciones `obtener_*` en `api.py`
3. Documentar el formato esperado
4. Probar la conexión

---

**Última actualización**: Febrero 2026  
**Versión**: 1.0.0
