from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.db import db 
import atexit
import os

IP = os.getenv("FLASK_HOST", "0.0.0.0")
PORT = os.getenv("FLASK_PORT", "8080")

def create_app():
    # Obtener URL de base de datos desde variable de entorno o usar default
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "contra123")
    db_host = os.getenv("DB_HOST", "db")  # 'db' es el nombre del servicio en docker-compose
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "fleet_manager")
    
    DATABASE_URI = f'mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '110-306-725'
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from .routes.api import api, obtener_vehiculos_cosemar, obtener_coordenadas_cosemar, obtener_vehiculos_linksur, obtener_coordenadas_linksur
        from .routes.main import main
        from .routes.crud import crud
        from .routes.creation import creation
        from .routes.auth import auth
        from .routes.api_config import api_config
        
        app.register_blueprint(api)
        app.register_blueprint(main)
        app.register_blueprint(crud)
        app.register_blueprint(creation)
        app.register_blueprint(auth)
        app.register_blueprint(api_config)

        db.create_all()

        scheduler = BackgroundScheduler()

        # Comentar temporalmente los jobs que requieren datos externos
        # scheduler.add_job(func=lambda: obtener_vehiculos_linksur(app), trigger=IntervalTrigger(seconds=5), id='job_datos', replace_existing=True)
        # scheduler.add_job(func=lambda: obtener_coordenadas_linksur(app), trigger=IntervalTrigger(seconds=10), id='job_coordenadas', replace_existing=True)
        # scheduler.add_job(func=lambda: obtener_vehiculos_cosemar(app), trigger=IntervalTrigger(seconds=5), id='job_vehiculos', replace_existing=True)
        # scheduler.add_job(func=lambda: obtener_coordenadas_cosemar(app), trigger=IntervalTrigger(seconds=10), id='job_trayecto', replace_existing=True)

        scheduler.start()

        atexit.register(lambda: scheduler.shutdown())

    return app