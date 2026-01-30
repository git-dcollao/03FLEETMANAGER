@echo off
REM Procesar datos de Chile para OSRM

setlocal enabledelayedexpansion

set "dataDir=%~dp0osrm-data"
set "file=chile-latest.osm.pbf"

echo.
echo ========================================
echo   Procesando Chile para OSRM
echo ========================================
echo.

if not exist "%dataDir%\%file%" (
    echo [ERROR] Archivo no encontrado: %dataDir%\%file%
    pause
    exit /b 1
)

echo [*] Paso 1: Extrayendo datos...
docker run -v "%dataDir%:/data" osrm/osrm-backend osrm-extract --profile /usr/local/share/osrm/profiles/car.lua /data/%file%

echo.
echo [*] Paso 2: Particionando datos...
docker run -v "%dataDir%:/data" osrm/osrm-backend osrm-partition /data/chile-latest.osrm

echo.
echo [*] Paso 3: Personalizando datos...
docker run -v "%dataDir%:/data" osrm/osrm-backend osrm-customize /data/chile-latest.osrm

echo.
echo ========================================
echo   [OK] Procesamiento completado
echo ========================================
echo.

echo [*] Iniciando aplicacion...
cd /d "%~dp0"
docker-compose up -d

echo.
echo [*] Esperando a que OSRM inicie...
timeout /t 5

echo.
echo [OK] Accede a: http://localhost:8080/ver_trayecto/4
echo.

pause
