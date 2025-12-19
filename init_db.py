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
        
        # Crear empresas
        empresa1 = Empresa(nombre_empresa="COSEMAR")
        empresa2 = Empresa(nombre_empresa="HOSPICIO")
        empresa3 = Empresa(nombre_empresa="MUNICIPALIDAD")
        db.session.add_all([empresa1, empresa2, empresa3])
        db.session.commit()
        
        # Crear departamentos
        dpto1 = DptoEmpresa(nombre_dpto_empresa="Sistemas", id_empresa=empresa1.id_empresa)
        dpto2 = DptoEmpresa(nombre_dpto_empresa="Logística", id_empresa=empresa1.id_empresa)
        dpto3 = DptoEmpresa(nombre_dpto_empresa="Administración", id_empresa=empresa2.id_empresa)
        db.session.add_all([dpto1, dpto2, dpto3])
        db.session.commit()
        
        # Crear cargos
        cargo1 = Cargo(nombre_cargo="Administrador", id_dpto_empresa=dpto1.id_dpto_empresa)
        cargo2 = Cargo(nombre_cargo="Operador", id_dpto_empresa=dpto2.id_dpto_empresa)
        cargo3 = Cargo(nombre_cargo="Supervisor", id_dpto_empresa=dpto3.id_dpto_empresa)
        db.session.add_all([cargo1, cargo2, cargo3])
        db.session.commit()
        
        # Crear personal
        personal1 = Personal(
            rut_personal="12345678-9",
            nombre_personal="Admin",
            apellido_paterno="Usuario",
            apellido_materno="Sistema",
            fecha_contrato="2025-01-01",
            fono="912345678",
            estado="activo",
            id_cargo=cargo1.id_cargo
        )
        personal2 = Personal(
            rut_personal="11222333-4",
            nombre_personal="Juan",
            apellido_paterno="Pérez",
            apellido_materno="López",
            fecha_contrato="2025-01-05",
            fono="987654321",
            estado="activo",
            id_cargo=cargo2.id_cargo
        )
        personal3 = Personal(
            rut_personal="22333444-5",
            nombre_personal="María",
            apellido_paterno="García",
            apellido_materno="Martínez",
            fecha_contrato="2025-01-10",
            fono="998765432",
            estado="activo",
            id_cargo=cargo3.id_cargo
        )
        db.session.add_all([personal1, personal2, personal3])
        db.session.commit()
        
        # Crear roles de usuario
        rol_admin = RolUsuario(nombre_rol_usuario="Administrador")
        rol_operador = RolUsuario(nombre_rol_usuario="Operador")
        rol_supervisor = RolUsuario(nombre_rol_usuario="Supervisor")
        db.session.add_all([rol_admin, rol_operador, rol_supervisor])
        db.session.commit()
        
        # Crear usuarios
        usuario_admin = Usuario(
            username="admin",
            password=generate_password_hash("admin123"),
            staff=1,
            id_rol_usuario=rol_admin.id_rol_usuario,
            id_personal=personal1.id_personal
        )
        usuario_juan = Usuario(
            username="juan",
            password=generate_password_hash("juan123"),
            staff=0,
            id_rol_usuario=rol_operador.id_rol_usuario,
            id_personal=personal2.id_personal
        )
        usuario_maria = Usuario(
            username="maria",
            password=generate_password_hash("maria123"),
            staff=0,
            id_rol_usuario=rol_supervisor.id_rol_usuario,
            id_personal=personal3.id_personal
        )
        db.session.add_all([usuario_admin, usuario_juan, usuario_maria])
        db.session.commit()
        
        print("\n" + "="*50)
        print("✓ BASE DE DATOS INICIALIZADA EXITOSAMENTE")
        print("="*50)
        print("\nEmpresas creadas:")
        print("  • COSEMAR")
        print("  • HOSPICIO")
        print("  • MUNICIPALIDAD")
        print("\nCredenciales de acceso:")
        print("  Usuario: admin | Contraseña: admin123")
        print("  Usuario: juan | Contraseña: juan123")
        print("  Usuario: maria | Contraseña: maria123")
        print("="*50 + "\n")
    else:
        print("✓ La base de datos ya tiene datos inicializados.")
        print("\nSi deseas resetear, elimina el volumen de docker:")
        print("  docker-compose down -v")
        print("  docker-compose up -d")
