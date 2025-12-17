# @app.route('/perfil')
# def perfil():
#     if 'username' in session:
#         username = session['username']
#         usuario = Usuario.query.filter_by(username=username).first()
#         personal_usuario = usuario.personal.id_personal
#         cargo_usuario = usuario.personal.cargo.cargo.id_cargo
#         departamento_usuario = usuario.personal.cargo.dpto_empresa.id_dpto_empresa
#         empresa_usuario = usuario.personal.cargo.dpto_empresa.empresa.id_empresa
#         flota_usuario = usuario.personal.cargo.dpto_empresa.flota.id_flota

#         if usuario and usuario.personal:
#             nombre_personal = usuario.personal.nombre_personal + " " + usuario.personal.apellido_paterno + " " + usuario.personal.apellido_materno
#             nombre_empresa = usuario.personal.cargo.dpto_empresa.empresa.nombre_empresa
#             departamento_usuario = usuario.personal.cargo.dpto_empresa.nombre_dpto_empresa
#         else:
#             nombre_personal = None
#             nombre_empresa = None

#         return render_template('.html', username=username, 
#                                 nombre_personal=nombre_personal, 
#                                 nombre_empresa=nombre_empresa)
#     else:
#         return redirect(url_for('login'))