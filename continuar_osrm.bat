@echo off
REM Script para continuar procesamiento de OSRM despues de la extraccion

setlocal enabledelayedexpansion

set "osrmDataDir=%~dp0osrm-data"

echo [*] Paso 1: Extrayendo datos de Chile...
docker run -v "%osrmDataDir%:/data" osrm/osrm-backend osrm-extract --profile /usr/local/share/osrm/profiles/car.lua /data/chile-latest.osm.pbf
if !errorlevel! neq 0 (
    echo [ERROR] Fallo en la extraccion
    pause
    exit /b 1
)

echo.
echo [OK] Extraccion completada
echo.

echo [*] Paso 2: Particionando datos...
docker run -v "%osrmDataDir%:/data" osrm/osrm-backend osrm-partition /data/chile-latest.osrm
if !errorlevel! neq 0 (
    echo [ERROR] Fallo en la particion
    pause
    exit /b 1
)

echo.
echo [OK] Particion completada
echo.

echo [*] Paso 3: Personalizando datos...
docker run -v "%osrmDataDir%:/data" osrm/osrm-backend osrm-customize /data/chile-latest.osrm
if !errorlevel! neq 0 (
    echo [ERROR] Fallo en la personalizacion
    pause
    exit /b 1
)

echo.
echo ========================================
echo   [OK] Todos los pasos completados
echo ========================================
echo.

echo Archivos generados:
for %%f in ("%osrmDataDir%\chile-latest.osrm*") do (
    echo   - %%~nf
)

echo.
echo Proximos pasos:
echo   1. docker-compose up -d
echo   2. Abre http://localhost:8080/ver_trayecto/4
echo.

pause
