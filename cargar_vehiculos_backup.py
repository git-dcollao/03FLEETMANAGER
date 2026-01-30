#!/usr/bin/env python3
"""
Script para cargar datos de vehículos desde el backup SQL
a la base de datos actual mediante requests HTTP
"""

import requests
import json
from urllib.parse import urljoin

# Configuración
BASE_URL = "http://localhost:8080"
SESSION_URL = f"{BASE_URL}/login"
CREAR_VEHICULO_URL = f"{BASE_URL}/crear_vehiculo"

# Datos de vehículos del backup
# id_dtv=9: "3/4" (Detalle Tipo Vehículo)
# id_flota=7: "Basureros" (Flota del departamento DAF)
VEHICULOS_BACKUP = [
    {
        'patente': 'YL 3334',
        'gps': '864035050615344',
        'estado': 'Activo',
        'id_dtv': '9',  # Detalle TV: "3/4"
        'id_flota': '7',  # Flota: "Basureros"
        'restriccion': '1'  # Sin restricción
    },
    {
        'patente': 'ZD 7233',
        'gps': '860856040481560',
        'estado': 'Activo',
        'id_dtv': '9',  # Detalle TV: "3/4"
        'id_flota': '7',  # Flota: "Basureros"
        'restriccion': '1'  # Sin restricción
    },
    {
        'patente': 'JPJB 38',
        'gps': '864035051052281',
        'estado': 'Activo',
        'id_dtv': '9',  # Detalle TV: "3/4"
        'id_flota': '7',  # Flota: "Basureros"
        'restriccion': '1'  # Sin restricción
    }
]

def main():
    print("=" * 60)
    print("CARGADOR DE VEHÍCULOS DESDE BACKUP")
    print("=" * 60)
    
    # Solicitar credenciales
    username = input("\nIngrese su usuario: ").strip()
    password = input("Ingrese su contraseña: ").strip()
    
    if not username or not password:
        print("❌ Usuario o contraseña vacíos")
        return
    
    # Crear sesión
    session = requests.Session()
    
    print("\n🔐 Autenticando...")
    try:
        # Intentar login
        response = session.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ No se puede conectar al servidor")
            print(f"   Estado: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return
    
    print("✅ Conectado al servidor\n")
    
    # Cargar vehículos
    print("Vehículos a cargar:")
    print("-" * 60)
    for i, v in enumerate(VEHICULOS_BACKUP, 1):
        print(f"{i}. Patente: {v['patente']:15} | GPS: {v['gps']}")
    print("-" * 60)
    
    confirmar = input("\n¿Desea cargar estos vehículos? (s/n): ").strip().lower()
    if confirmar != 's':
        print("❌ Operación cancelada")
        return
    
    # Cargar cada vehículo
    print("\n📥 Iniciando carga de vehículos...\n")
    
    for idx, vehiculo in enumerate(VEHICULOS_BACKUP, 1):
        try:
            print(f"[{idx}/{len(VEHICULOS_BACKUP)}] Cargando: {vehiculo['patente']}...", end=" ")
            
            data = {
                'patente': vehiculo['patente'],
                'gps': vehiculo['gps'],
                'estado': vehiculo['estado'],
                'detalles_tv': vehiculo['id_dtv'],
                'flota': vehiculo['id_flota'],
                'restriccion': vehiculo['restriccion']
            }
            
            response = session.post(CREAR_VEHICULO_URL, data=data)
            
            if response.status_code == 200:
                print("✅ OK")
            else:
                print(f"⚠️  Código: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ PROCESO COMPLETADO")
    print("=" * 60)
    print("\nPuede acceder a los vehículos en:")
    print(f"   {BASE_URL}/crear_vehiculo")
    print()

if __name__ == "__main__":
    main()
