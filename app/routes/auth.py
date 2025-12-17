from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from app.db import db 
from app.models import Usuario, RolUsuario, Personal, Cargo, DptoEmpresa
from werkzeug.security import check_password_hash, generate_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/registrar', methods=['GET', 'POST'])
def crear_usuario():
    if 'username' in session:
        username = session['username']
        usuario = Usuario.query.filter_by(username=username).first()
        departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
        if request.method == 'POST':
            username = request.form['username']
            password_plano = request.form['password']
            rol_usuario = request.form['rol_usuario']
            id_personal = request.form['personal']

            usuario_existente_username = Usuario.query.filter_by(username=username).first()
            if usuario_existente_username:
                flash('El nombre de usuario ya está en uso. Por favor, elija otro.')
                return redirect(url_for('creation.crear_usuario'))

            password_encriptada = generate_password_hash(password_plano)

            nuevo_usuario = Usuario(username=username, 
                                    password=password_encriptada,
                                    id_rol_usuario=rol_usuario,
                                    id_personal=id_personal)
            
            db.session.add(nuevo_usuario)
            db.session.commit()

            return redirect(url_for('main.menu_personal'))
        
        rol_usuario = RolUsuario.query.filter(RolUsuario.id_rol_usuario >= 1).all()
        personal = Personal.query.join(Cargo).join(DptoEmpresa).filter(DptoEmpresa.id_dpto_empresa == departamento_usuario, Personal.id_personal >= 1).all()

        return render_template('auth/register.html', rol_usuario=rol_usuario, personales=personal)
    else:
        return redirect(url_for('auth.login'))
    
@auth.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('main.index'))
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            usuario = Usuario.query.filter_by(username=username).first()

            if usuario and check_password_hash(usuario.password, password):
                session['username'] = usuario.username
                
                return redirect(url_for('main.index'))
            else:
                return render_template('auth/login.html', error='Usuario o contraseña incorrectos')

        return render_template('auth/login.html')

@auth.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('auth.login'))