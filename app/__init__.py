from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config


db = SQLAlchemy()

def create_app(config_class=Config):
    """Comme son nom l'indique cette fonction permet de créer l'application grace à certains pramametre bdd et les blueprints importés"""
    app = Flask(__name__)
    app.secret_key = 'keypass'
    app.config.from_object(config_class)
    db.init_app(app)
    from app.hosts import host_bp
    app.register_blueprint(host_bp)
    return app

