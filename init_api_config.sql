-- Script para inicializar configuraciones de API de ejemplo
-- Ejecutar después de crear las tablas

-- LINKSUR - Vehículos
INSERT INTO api_config (
    nombre_proveedor,
    tipo_api,
    url,
    auth_type,
    auth_value,
    header_name,
    activo,
    id_dpto_empresa,
    intervalo_segundos,
    descripcion
) VALUES (
    'LINKSUR',
    'vehiculos',
    'https://smartgps.gpsserver.xyz/v3/apis/global_api/v3.0.0/public/index.php/obtener_posicion_actual/{token}',
    'token',
    'e0a9528e7a5f181568f797e7f2d7c355',
    NULL,
    FALSE,
    7,
    5,
    'API de SmartGPS para obtener lista de vehículos LINKSUR'
);

-- LINKSUR - Coordenadas
INSERT INTO api_config (
    nombre_proveedor,
    tipo_api,
    url,
    auth_type,
    auth_value,
    header_name,
    activo,
    id_dpto_empresa,
    intervalo_segundos,
    descripcion
) VALUES (
    'LINKSUR',
    'coordenadas',
    'https://smartgps.gpsserver.xyz/v3/apis/global_api/v3.0.0/public/index.php/obtener_posicion_actual/{token}',
    'token',
    'e0a9528e7a5f181568f797e7f2d7c355',
    NULL,
    FALSE,
    7,
    10,
    'API de SmartGPS para obtener coordenadas GPS de vehículos LINKSUR'
);

-- COSEMAR - Vehículos
INSERT INTO api_config (
    nombre_proveedor,
    tipo_api,
    url,
    auth_type,
    auth_value,
    header_name,
    activo,
    id_dpto_empresa,
    intervalo_segundos,
    descripcion
) VALUES (
    'COSEMAR',
    'vehiculos',
    'https://api.inducomgps.com/v1/vehiculos?fields[]=patente',
    'api_key',
    '71c627fc-8987-46b9-93f8-4d257a2a26fc',
    'Authorization-api-key',
    FALSE,
    7,
    5,
    'API de InducomGPS para obtener lista de vehículos COSEMAR'
);

-- COSEMAR - Coordenadas  
INSERT INTO api_config (
    nombre_proveedor,
    tipo_api,
    url,
    auth_type,
    auth_value,
    header_name,
    activo,
    id_dpto_empresa,
    intervalo_segundos,
    descripcion
) VALUES (
    'COSEMAR',
    'coordenadas',
    'https://api.inducomgps.com/v1/vehiculos/{id_gps}/posiciones?start={inicio}&end={fin}',
    'api_key',
    '71c627fc-8987-46b9-93f8-4d257a2a26fc',
    'Authorization-api-key',
    FALSE,
    7,
    10,
    'API de InducomGPS para obtener coordenadas GPS de vehículos COSEMAR. Nota: Esta API requiere parámetros dinámicos'
);
