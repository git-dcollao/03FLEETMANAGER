from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.db import db
from app.models import ApiConfig, DptoEmpresa
from datetime import datetime

api_config = Blueprint('api_config', __name__)

@api_config.route('/apis')
def listar_apis():
    """Lista todas las configuraciones de API"""
    apis = ApiConfig.query.all()
    return render_template('api_config/listar_apis.html', apis=apis)

@api_config.route('/apis/nueva', methods=['GET', 'POST'])
def crear_api():
    """Crear una nueva configuración de API"""
    if request.method == 'POST':
        try:
            nueva_api = ApiConfig(
                nombre_proveedor=request.form['nombre_proveedor'],
                tipo_api=request.form['tipo_api'],
                url=request.form['url'],
                auth_type=request.form['auth_type'],
                auth_value=request.form['auth_value'],
                header_name=request.form.get('header_name'),
                activo=request.form.get('activo') == 'on',
                id_dpto_empresa=int(request.form['id_dpto_empresa']),
                intervalo_segundos=int(request.form.get('intervalo_segundos', 10)),
                descripcion=request.form.get('descripcion')
            )
            
            db.session.add(nueva_api)
            db.session.commit()
            
            flash('Configuración de API creada exitosamente', 'success')
            return redirect(url_for('api_config.listar_apis'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la configuración: {str(e)}', 'danger')
    
    # GET - Mostrar formulario
    departamentos = DptoEmpresa.query.all()
    return render_template('api_config/crear_api.html', departamentos=departamentos)

@api_config.route('/apis/editar/<int:id_api>', methods=['GET', 'POST'])
def editar_api(id_api):
    """Editar una configuración de API existente"""
    api = ApiConfig.query.get_or_404(id_api)
    
    if request.method == 'POST':
        try:
            api.nombre_proveedor = request.form['nombre_proveedor']
            api.tipo_api = request.form['tipo_api']
            api.url = request.form['url']
            api.auth_type = request.form['auth_type']
            api.auth_value = request.form['auth_value']
            api.header_name = request.form.get('header_name')
            api.activo = request.form.get('activo') == 'on'
            api.id_dpto_empresa = int(request.form['id_dpto_empresa'])
            api.intervalo_segundos = int(request.form.get('intervalo_segundos', 10))
            api.descripcion = request.form.get('descripcion')
            
            db.session.commit()
            
            flash('Configuración de API actualizada exitosamente', 'success')
            return redirect(url_for('api_config.listar_apis'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la configuración: {str(e)}', 'danger')
    
    # GET - Mostrar formulario con datos actuales
    departamentos = DptoEmpresa.query.all()
    return render_template('api_config/editar_api.html', api=api, departamentos=departamentos)

@api_config.route('/apis/eliminar/<int:id_api>', methods=['POST'])
def eliminar_api(id_api):
    """Eliminar una configuración de API"""
    try:
        api = ApiConfig.query.get_or_404(id_api)
        db.session.delete(api)
        db.session.commit()
        flash('Configuración de API eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la configuración: {str(e)}', 'danger')
    
    return redirect(url_for('api_config.listar_apis'))

@api_config.route('/apis/toggle/<int:id_api>', methods=['POST'])
def toggle_api(id_api):
    """Activar/Desactivar una API"""
    try:
        api = ApiConfig.query.get_or_404(id_api)
        api.activo = not api.activo
        db.session.commit()
        
        estado = 'activada' if api.activo else 'desactivada'
        flash(f'API {api.nombre_proveedor} {estado} exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar el estado: {str(e)}', 'danger')
    
    return redirect(url_for('api_config.listar_apis'))

@api_config.route('/apis/test/<int:id_api>', methods=['POST'])
def test_api(id_api):
    """Probar conexión a una API"""
    import requests
    
    api = ApiConfig.query.get_or_404(id_api)
    
    try:
        headers = {}
        url = api.url
        
        # Configurar autenticación según el tipo
        if api.auth_type == 'token':
            # Token en URL
            if '{token}' in url:
                url = url.replace('{token}', api.auth_value)
        elif api.auth_type == 'api_key' and api.header_name:
            headers[api.header_name] = api.auth_value
        elif api.auth_type == 'bearer':
            headers['Authorization'] = f'Bearer {api.auth_value}'
        
        # Hacer la petición
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Conexión exitosa',
                'status_code': response.status_code,
                'data_preview': str(response.json())[:200] if response.headers.get('content-type', '').startswith('application/json') else 'OK'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Error HTTP {response.status_code}',
                'status_code': response.status_code
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error de conexión: {str(e)}'
        })
