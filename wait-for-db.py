#!/usr/bin/env python3
import sys
import time
import subprocess
import os

db_host = sys.argv[1] if len(sys.argv) > 1 else "db"
db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD", "contra123")
max_retries = 30
retry_count = 0

print(f"Esperando que MySQL esté disponible en {db_host}...")

try:
    import MySQLdb
    while retry_count < max_retries:
        try:
            conn = MySQLdb.connect(
                host=db_host,
                user=db_user,
                passwd=db_password
            )
            conn.close()
            print("✓ MySQL está disponible")
            break
        except Exception as e:
            pass
        
        retry_count += 1
        print(f"Intento {retry_count}/{max_retries}...")
        time.sleep(1)
except ImportError:
    # Si MySQLdb no está disponible, usar una simple prueba de ping TCP
    import socket
    while retry_count < max_retries:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((db_host, 3306))
            sock.close()
            if result == 0:
                print("✓ MySQL está disponible")
                break
        except Exception as e:
            pass
        
        retry_count += 1
        print(f"Intento {retry_count}/{max_retries}...")
        time.sleep(1)

if retry_count >= max_retries:
    print("✗ No se pudo conectar a MySQL después de varios intentos")
    sys.exit(1)

# Ejecutar el comando pasado como argumento
if len(sys.argv) > 2:
    os.execvp(sys.argv[2], sys.argv[2:])

