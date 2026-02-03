# 🚛 Fleet Manager

Sistema de gestión y monitoreo de flotas vehiculares en tiempo real, con visualización de trayectos, zonas de trabajo y análisis de rutas optimizadas.

## 📋 Descripción

Fleet Manager es una aplicación web desarrollada en Flask que permite:

- 📍 **Monitoreo en tiempo real** de vehículos
- 🗺️ **Visualización de trayectos** con rutas optimizadas usando OSRM
- 🎯 **Gestión de zonas** (cuadrantes, sectores, cercos, zonas de trabajo)
- 📊 **Análisis de recorridos** con mapas de calor
- ⏯️ **Animación de trayectos** con controles interactivos
- 🔄 **Integración con APIs** externas para obtención de datos GPS
- � **Gestión dinámica de APIs** de proveedores GPS sin modificar código
- �📈 **Reportes y estadísticas** de desempeño vehicular

## 🛠️ Tecnologías

### Backend
- **Flask 3.0.3** - Framework web
- **SQLAlchemy** - ORM para base de datos
- **MySQL 8.0** - Base de datos
- **APScheduler** - Programación de tareas
- **Pandas & NumPy** - Procesamiento de datos

### Frontend
- **Leaflet.js** - Mapas interactivos
- **Bootstrap 5** - Framework CSS
- **JavaScript ES6** - Interactividad

### Servicios
- **OSRM** - Open Source Routing Machine para enrutamiento
- **Docker & Docker Compose** - Contenedorización

## 📁 Estructura del Proyecto

```
03FLEETMANAGER/
├── app/
│   ├── routes/          # Blueprints de Flask
│   │   ├── main.py      # Rutas principales
│   │   ├── api.py       # Endpoints API
│   │   ├── api_config.py # Gestión de APIs (NUEVO)
│   │   ├── crud.py      # Operaciones CRUD
│   │   ├── creation.py  # Creación de entidades
│   │   └── auth.py      # Autenticación
│   ├── templates/       # Plantillas HTML
│   │   ├── api_config/  # Templates gestión APIs (NUEVO)
│   │   └── ...
│   ├── static/          # CSS, JS, imágenes
│   ├── models.py        # Modelos de base de datos
│   ├── db.py           # Configuración de DB
│   └── __init__.py     # Inicialización de la app
├── osrm-data/          # Datos de mapas OSRM
├── 00-DOCS/            # Documentación
├── docker-compose.yml  # Configuración de servicios
├── Dockerfile          # Imagen de la aplicación
├── requirements.txt    # Dependencias Python
└── init_db.py         # Inicialización de BD
```

## 🚀 Instalación y Configuración

### Requisitos Previos

- Docker Desktop instalado y ejecutándose
- Python 3.11+ (para desarrollo local)
- ~2 GB de espacio en disco libre
- Git

### 1. Clonar el Repositorio

```bash
git clone https://github.com/git-dcollao/03FLEETMANAGER.git
cd 03FLEETMANAGER
```

### 2. Configurar OSRM (Servicio de Rutas)

**Primera vez - Descargar y procesar mapas:**

```powershell
# En Windows PowerShell
.\descargar_mapas_osrm.bat
```

Este proceso:
- Descarga mapas de Chile/Sudamérica (~500 MB)
- Procesa los datos con OSRM (15-30 minutos)
- Genera archivos `.osrm` listos para usar

Ver [OSRM_SETUP.md](OSRM_SETUP.md) para más detalles.

### 3. Iniciar los Servicios

```powershell
# Construir e iniciar todos los contenedores
docker-compose down
docker-compose build
docker-compose up -d
```

Esto iniciará:
- **MySQL** en puerto `3307`
- **OSRM** en puerto `5555`
- **Flask App** en puerto `8080`

### 4. Verificar que los Servicios Están Corriendo

```powershell
docker-compose ps
```

Deberías ver:
- `fleet_manager_db` - healthy
- `fleet_manager_osrm` - running
- `fleet_manager_app` - running

### 5. Acceder a la Aplicación

Abre tu navegador en:
```
http://localhost:8080
```

## 🎮 Uso

### Visualizar Trayectos

1. Navega a **Ver Trayecto** desde el menú principal
2. Selecciona un vehículo
3. Elige fecha y rango horario
4. Usa los botones:
   - **Graficar Trayecto** - Muestra la ruta completa
   - **Animar Trayecto** - Reproduce el recorrido con animación
   - **Mapa de Calor** - Visualiza zonas de mayor tránsito

### Controles de Animación

Cuando inicias una animación, aparece un panel flotante con:
- ⏸️ **Pausar** - Detiene la animación temporalmente
- ▶️ **Reanudar** - Continúa desde donde se pausó
- El panel es **arrastrable** - muévelo a cualquier parte del mapa

### Gestión de Zonas

- **Cuadrantes** - Divisiones territoriales (azul)
- **Sectores** - Áreas operativas (verde)
- **Zonas de Trabajo** - Áreas específicas (rojo)
- **Cercos** - Límites de seguridad (negro)

### 🔌 Gestión de APIs de Proveedores GPS (NUEVO)

Fleet Manager ahora permite administrar configuraciones de APIs de manera dinámica:

1. Ve a **Administración de Datos** → **🔌 Configurar APIs**
2. **Agregar nuevo proveedor**:
   - Click en "➕ Nueva API"
   - Completa: Nombre, Tipo (vehículos/coordenadas), URL, Token/API Key
   - Selecciona tipo de autenticación (token, api_key, bearer)
   - Activa/desactiva según necesidad
3. **Probar conexión**: Click en 🔍 para verificar conectividad
4. **Activar/Pausar**: Controla qué APIs están consultándose
5. **Editar/Eliminar**: Modifica configuraciones sin tocar código

**Beneficios:**
- ✅ No más tokens hardcodeados en el código
- ✅ Agregar proveedores GPS sin programar
- ✅ Activar/desactivar APIs en tiempo real
- ✅ Probar conexiones desde la interfaz

Ver documentación completa: [API_CONFIG_MODULE.md](00-DOCS/API_CONFIG_MODULE.md)
- **Cercos** - Límites de seguridad (negro)

## 🔧 Desarrollo Local

### Configurar Entorno Virtual

```powershell
# Crear entorno virtual
python -m venv venv

# Activar
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Variables de Entorno

El archivo `docker-compose.yml` contiene:

```yaml
DB_USER: root
DB_PASSWORD: contra123
DB_HOST: db
DB_PORT: 3306
DB_NAME: fleet_manager
OSRM_HOST: osrm
OSRM_PORT: 5000
```

### Ver Logs

```powershell
# Logs de la aplicación Flask
docker-compose logs -f app

# Logs de MySQL
docker-compose logs -f db

# Logs de OSRM
docker-compose logs -f osrm
```

## 📊 Base de Datos

### Inicializar Base de Datos

```powershell
# Ejecutar desde dentro del contenedor
docker exec -it fleet_manager_app python init_db.py
```

### Modelos Principales

- **Vehiculo** - Datos de vehículos
- **Coordenada** - Puntos GPS
- **Area** - Zonas geográficas
- **Programacion** - Rutas programadas
- **Trayecto** - Historial de recorridos

## 🐛 Solución de Problemas

### OSRM no responde

```powershell
# Verificar que los archivos .osrm existen
ls .\osrm-data\*.osrm

# Reiniciar solo OSRM
docker-compose restart osrm
```

### Error de conexión a MySQL

```powershell
# Verificar que MySQL está healthy
docker-compose ps db

# Reiniciar base de datos
docker-compose restart db
```

### Cambios en código no se reflejan

```powershell
# Reconstruir la imagen
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Docker

```powershell
# Detener todo
docker-compose down

# Reconstruir
docker-compose build

# Iniciar en modo detached
docker-compose up -d
```

### Python

```powershell
# Actualizar requirements
pip freeze > requirements.txt

# Instalar nueva dependencia
pip install nombre-paquete
```

## 📄 Licencia

Este proyecto es de uso interno.

## 👥 Autores

- **Daniel Collao** - [git-dcollao](https://github.com/git-dcollao)

## 📞 Soporte

Para problemas o preguntas:
- Abre un issue en GitHub
- Consulta la documentación en `/00-DOCS`

## 🔄 Estado del Proyecto

🟢 **Activo** - En desarrollo continuo

---

**Versión:** 1.0.0  
**Última actualización:** Febrero 2026
