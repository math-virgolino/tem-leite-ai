from flask import Flask
from app.extensions import db, login_manager
from config import Config
from sqlalchemy import event
from sqlite3 import Connection as SQLite3Connection

def create_app():
    app = Flask(__name__)
    
    # Carregar as configurações do arquivo config.py
    app.config.from_object(Config)

    # Inicializar as extensões
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # Define a view de login

    # Configurar o SQLite para usar o modo WAL
    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, SQLite3Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.close()

        # Criar as tabelas do banco de dados
        db.create_all()

    # Registrar as rotas
    from app.routes import init_routes
    init_routes(app)

    return app