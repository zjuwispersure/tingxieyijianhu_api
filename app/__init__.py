from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from .models.database import db
from .api.dictation import dictation_bp

migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    from .api import init_app
    init_app(app)
    
    return app 