import os
from flask import Flask, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from ozon.config import config
from flask_migrate import Migrate


bootstrap = Bootstrap()
login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    return app


app = create_app(os.getenv('FLASK_CONFIG') or 'default')


from .models import *
from .main.views import api
from .users.views import users


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(api)
app.register_blueprint(users)



