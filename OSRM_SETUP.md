# 🗺️ Instalación de OSRM para Fleet Manager

## ¿Qué es OSRM?

**OSRM** (Open Source Routing Machine) es un servicio de enrutamiento de código abierto que calcula rutas óptimas en base a los datos de OpenStreetMap. Permite dibujar recorridos reales en lugar de líneas rectas.

## Instalación Paso a Paso

### 1. Descargar y Procesar Mapas (Primera vez)

Ejecuta el script de descarga:

```powershell
.\descargar_mapas_osrm.ps1
```

Este script:
- ✅ Descarga ~500 MB de mapas de Sudamérica
- ✅ Procesa los datos con OSRM (15-30 min)
- ✅ Genera archivos listos para usar

**Requisitos:**
- Docker instalado y corriendo
- ~1.5 GB de espacio en disco libre

### 2. Iniciar los Contenedores

```powershell
docker-compose down  # Detener si estaban corriendo
docker-compose up -d  # Iniciar con OSRM
```

Espera a que todos los servicios estén listos:
```powershell
docker-compose ps
```

### 3. Verificar que OSRM está activo

```powershell
curl http://localhost:5000/status
```

Deberías ver algo como:
```json
{"status":0,"message":"Ok. Matching service is ready."}
```

### 4. Usar en la Aplicación

La aplicación ahora usará automáticamente OSRM. Cuando grafaces un trayecto en `/ver_trayecto/4`:

- **Líneas reales**: Siguen las calles de OpenStreetMap
- **Fallback automático**: Si OSRM no responde, usa líneas directas
- **Logs en navegador**: Abre F12 para ver detalles de la consulta

## Alternativas

### Opción A: Descargar mapas manualmente

Si el script falla, descarga manualmente:

1. Ve a: https://download.geofabrik.de/south-america.html
2. Descarga `south-america-latest.osm.pbf`
3. Guarda en: `osrm-data/south-america-latest.osm.pbf`
4. Ejecuta el procesamiento:

```powershell
$osrmDir = "osrm-data"
docker run -v "${osrmDir}:/data" osrm/osrm-backend osrm-extract -p /profiles/car.lua /data/south-america-latest.osm.pbf
docker run -v "${osrmDir}:/data" osrm/osrm-backend osrm-partition /data/south-america-latest.osrm
docker run -v "${osrmDir}:/data" osrm/osrm-backend osrm-customize /data/south-america-latest.osrm
```

### Opción B: Usar OSRM remoto (sin descargar)

Modifica el JavaScript en `app/templates/ver_trayecto.html`:

```javascript
const OSRM_HOST = "router.project-osrm.org";  // Servicio público
const OSRM_PORT = "80";
```

⚠️ **Nota**: El servicio público puede ser lento. Se recomienda local.

### Opción C: Usar otra región

Para mapas de otro país:
1. Descarga desde: https://download.geofabrik.de/
2. Cambia el nombre en `docker-compose.yml`
3. Procesa según el tamaño del archivo

## Estructura de carpetas

```
03FLEETMANAGER/
├── docker-compose.yml          (Servicios incluyendo OSRM)
├── descargar_mapas_osrm.ps1    (Script de descarga)
├── osrm-data/                  (Datos descargados)
│   ├── south-america-latest.osm.pbf
│   ├── south-america-latest.osrm
│   ├── south-america-latest.osrm.ebg
│   ├── south-america-latest.osrm.enw
│   ├── south-america-latest.osrm.fileIndex
│   ├── south-america-latest.osrm.metadata
│   └── south-america-latest.osrm.partition
└── app/templates/ver_trayecto.html (Usa OSRM aquí)
```

## Solución de Problemas

### OSRM no responde en `http://localhost:5000`

```powershell
# Verificar logs del contenedor
docker logs fleet_manager_osrm

# Reiniciar OSRM
docker restart fleet_manager_osrm
```

### Error: "Cannot find south-america-latest.osrm"

Asegúrate de que los datos están procesados:
```powershell
ls osrm-data/south-america-latest.osrm*
```

Si no existen, ejecuta el script de descarga nuevamente.

### La ruta es muy lenta

- Los primeros cálculos pueden tardar más
- Reduce el número de coordenadas (ej: cada 10 segundos en lugar de cada segundo)
- Usa un servidor OSRM más potente

### Docker rechaza volúmenes

En Windows, asegúrate que Docker está en "WSL 2 mode" y que tienes permisos en la carpeta.

## Performance

| Aspecto | Local | Remoto |
|--------|-------|--------|
| Velocidad | ⚡ Muy rápido | 🐢 Lento |
| Dependencias | Docker | Internet |
| Datos actuales | Descargados una vez | Siempre actuales |
| Privacidad | ✅ Privado | ❌ Se envían coords |

## Referencias

- **OSRM**: http://project-osrm.org/
- **OpenStreetMap**: https://www.openstreetmap.org/
- **Geofabrik**: https://www.geofabrik.de/
- **Docker OSRM**: https://hub.docker.com/r/osrm/osrm-backend

---

**Creado**: 27 de Enero de 2026  
**Modificado**: Por GitHub Copilot
