# Crear entorno virtual
    ' python -m venv venv '
# Activar entorno virtual
    ' ./venv/Scripts/activate ' 
# Desactivar entorno
    ' ./venv/Scripts/deactivate '
# Eliminar entorno virtual llamado "venv"
    ' Remove-Item -Recurse -Force venv '
# Instalar dependencias
    ' pip install Flask Flask-Migrate python-dotenv '
# Instalar requirements.txt 
    '  pip install -r requirements.txt '
# Guardar o actualizar requirements.txt
    ' pip freeze > requirements.txt '
    
# Detener servidores del docker-compose del proyecto
    ' docker-compose down 
     docker-compose build    
     docker-compose up -d '
# ewvisar archivo logs con errores del docker proyectos_app
    ' docker-compose logs proyectos_app '




# ------------------------------------------
#             GIT HUB 
# ------------------------------------------
# GitHub Copilot
# Para conectar tu repositorio local con GitHub y actualizar la rama master, sigue estos pasos:

# Configura tu repositorio local: Si aún no has inicializado un repositorio Git en tu proyecto, hazlo con el siguiente comando:
     ' git init '

# Agrega tu repositorio remoto: Si aún no has agregado tu repositorio remoto de GitHub, hazlo con el siguiente comando. Reemplaza URL_DEL_REPOSITORIO con la URL de tu repositorio en GitHub.
    ' git remote add origin URL_DEL_REPOSITORIO '

# Verifica la conexión con el repositorio remoto:
    ' git remote -v '
# Agrega los cambios a tu repositorio local:
    ' git add . '
# Confirma los cambios:
    ' git commit -m "Descripción de los cambios" '
# Actualiza la rama master en GitHub:
    ' git push origin master '
# Si es la primera vez que haces un push a la rama master, puede que necesites usar el siguiente comando:
    ' git push origin master '
# Esto configurará la rama master para que puedas usar simplemente git push en el futuro.
    ' git push -u origin master '
# Si necesitas autenticación, Git te pedirá tus credenciales de GitHub. También puedes configurar una clave SSH para evitar ingresar tus credenciales cada vez.

