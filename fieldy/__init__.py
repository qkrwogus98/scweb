from flask import Flask, redirect, url_for, request, send_from_directory

from fieldy.routes import main, api
from fieldy.database import db, initialize_db_tables
from fieldy.utils import is_active
from fieldy.extensions import login_manager, csrf#, moment

import os
from dotenv import load_dotenv

import datetime
import json

# from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()


def create_app(debug: bool):
    app = Flask(__name__.split('.')[0])  #, static_url_path='')
#    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    set_config(app, debug)
    register_extensions(app)
    register_blueprints(app)
    initialize_db_tables(app)
    return app


def set_config(app, debug):
    # if debug:
    app.config["SECRET_KEY"] = "{'=up%Dx-B7V3Ax3JZ5^"
    app.config["JSON_AS_ASCII"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = \
        f"{os.environ.get('DB_POSTGRES_SCHEMA')}://{os.environ.get('DB_POSTGRES_USERNAME')}:{os.environ.get('DB_POSTGRES_PASSWORD')}@{os.environ.get('DB_POSTGRES_HOST')}:{os.environ.get('DB_POSTGRES_PORT')}/{os.environ.get('DB_POSTGRES_NAME')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.json_provider_class.compact = True
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False  # removed in 2.3


def register_blueprints(app: Flask):
    # @app.before_request
    # def before_request():
    #     if request.host.startswith('s1.'):
    #         url = request.url.replace('//s1.', '//w1.', 1)
    #         url.replace('http://', 'https://', 1)
    #         return redirect(url)

    @app.route('/robots.txt')
    def static_from_root():
        return send_from_directory(app.static_folder, request.path[1:])

    # @app.route('/')
    # def main():
    #     return redirect(url_for('auth.signin'))

    # app.add_url_rule('/', 'auth.signin')

    app.register_blueprint(api.bp,      url_prefix='/api/v0')
    # app.register_blueprint(auth.bp,     url_prefix='/auth')
    app.register_blueprint(main.bp,    url_prefix='/')


def register_extensions(app: Flask):
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    # moment.init_app(app)

    app.jinja_env.globals.update(is_active=is_active)
    app.jinja_env.globals.update(datetime=datetime)
    app.jinja_env.globals.update(json=json)
