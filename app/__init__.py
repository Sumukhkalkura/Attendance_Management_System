"""Attendance Management System application factory."""
from flask import Flask, jsonify
from .db import init_db
from .routes import api


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY='dev-only-change-before-deployment', DATABASE='attendance.db', TESTING=False)
    if test_config:
        app.config.update(test_config)
    init_db(app)
    app.register_blueprint(api, url_prefix='/api')

    @app.get('/')
    def home():
        return jsonify(application='Attendance Management System', status='starter', note='Sprint 1 features under development')

    return app
