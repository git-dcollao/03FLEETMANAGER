@echo off
REM Script para descargar y procesar mapas OSRM
REM Descarga mapas de Sudamérica y los procesa para OSRM

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Descargador de Mapas para OSRM
echo ========================================
echo.

set "osrmDataDir=%~dp0osrm-data"
set "mapUrl=https://download.geofabrik.de/south-america-latest.osm.pbf"
set "mapFile=%osrmDataDir%\south-america-latest.osm.pbf"
set "osrmFile=%osrmDataDir%\south-america-latest.osrm"

echo Descargará aproximadamente 500 MB de datos de mapas.
echo El procesamiento puede tardar 15-30 minutos.
echo.
echo Carpeta destino: %osrmDataDir%
echo.

if exist "%osrmFile%" (
    echo [OK] Los datos OSRM ya estan preparados en: %osrmFile%
    echo.
    echo Puedes iniciar los contenedores con: docker-compose up -d
    pause
    exit /b 0
)

if exist "%mapFile%" (
    echo [OK] Archivo PBF encontrado. Saltando descarga...
    echo.
) else (
    echo [*] Descargando mapas de Sudamérica...
    echo URL: %mapUrl%
    echo.
    echo Esto puede tardar varios minutos...
    echo.
    
    powershell -Command "Invoke-WebRequest -Uri '%mapUrl%' -OutFile '%mapFile%' -UseBasicParsing" 
    
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Error durante la descarga
        echo.
        echo Descarga manual:
        echo 1. Ve a: https://download.geofabrik.de/south-america.html
        echo 2. Descarga: south-america-latest.osm.pbf
        echo 3. Guarda en: %osrmDataDir%\
        echo.
        pause
        exit /b 1
    )
    
    echo [OK] Descarga completada
    echo.
)

echo [*] Iniciando Docker para procesar los mapas...
echo Este paso puede tardar 15-30 minutos...
echo.

REM Verificar Docker
docker --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Docker no esta instalado o no esta en PATH
    pause
    exit /b 1
)

echo [OK] Docker encontrado
echo.

echo [*] Paso 1: Extrayendo datos...
docker run -v "%osrmDataDir%:/data" osrm/osrm-backend osrm-extract --profile /usr/local/share/osrm/profiles/car.lua /data/south-america-latest.osm.pbf
if !errorlevel! neq 0 (
    echo [ERROR] Fallo en la extraccion
    pause
    exit /b 1
)

echo.
echo [*] Paso 2: Particionando datos...
docker run -v "%osrmDataDir%:/data" osrm/osrm-backend osrm-partition /data/south-america-latest.osrm
if !errorlevel! neq 0 (
    echo [ERROR] Fallo en la particion
    pause
    exit /b 1
)

echo.
echo [*] Paso 3: Personalizando datos...
docker run -v "%osrmDataDir%:/data" osrm/osrm-backend osrm-customize /data/south-america-latest.osrm
if !errorlevel! neq 0 (
    echo [ERROR] Fallo en la personalizacion
    pause
    exit /b 1
)

echo.
echo ========================================
echo   [OK] Mapas listos para OSRM
echo ========================================
echo.

echo Archivos generados:
for %%f in ("%osrmDataDir%\south-america-latest.osrm*") do (
    echo   - %%~nf
)

echo.
echo Proximo paso:
echo   docker-compose up -d
echo.

pause
