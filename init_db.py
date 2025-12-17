#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de prueba
Ejecutar desde dentro del contenedor:
    docker-compose exec app python init_db.py
"""
import sys
import os
sys.path.insert(0, '/app')

from app import create_app
from app.db import db
from app.models import (
    Usuario, RolUsuario, Personal, Cargo, DptoEmpresa, Empresa
)
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Crear tablas
    print("✓ Creando tablas...")
    db.create_all()
    
    # Verificar si ya existen datos
    dpto_existente = DptoEmpresa.query.first()
    if not dpto_existente:
        print("✓ Inicializando datos de prueba...")
        
        # Crear empresa
        empresa = Empresa(nombre_empresa="Empresa Default")
        db.session.add(empresa)
        db.session.commit()
        
        # Crear departamento
        dpto = DptoEmpresa(nombre_dpto_empresa="Sistemas", id_empresa=empresa.id_empresa)
        db.session.add(dpto)
        db.session.commit()
        
        # Crear cargo
        cargo = Cargo(nombre_cargo="Administrador", id_dpto_empresa=dpto.id_dpto_empresa)
        db.session.add(cargo)
        db.session.commit()
        
        # Crear personal
        personal = Personal(
            nombre_personal="Admin",
            apellido_personal="Usuario",
            id_cargo=cargo.id_cargo
        )
        db.session.add(personal)
        db.session.commit()
        
        # Crear rol de usuario
        rol = RolUsuario(nombre_rol_usuario="Administrador")
        db.session.add(rol)
        db.session.commit()
        
        # Crear usuario admin
        usuario_admin = Usuario(
            username="admin",
            password=generate_password_hash("admin123"),
            id_rol_usuario=rol.id_rol_usuario,
            id_personal=personal.id_personal
        )
        db.session.add(usuario_admin)
        db.session.commit()
        
        print("\n" + "="*50)
        print("✓ BASE DE DATOS INICIALIZADA EXITOSAMENTE")
        print("="*50)
        print("\nCredenciales de acceso:")
        print("  Usuario: admin")
        print("  Contraseña: admin123")
        print("="*50 + "\n")
    else:
        print("✓ La base de datos ya tiene datos inicializados.")
        print("\nSi deseas resetear, elimina el volumen de docker:")
        print("  docker-compose down -v")
        print("  docker-compose up -d")
