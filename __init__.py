import datetime
import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo

from response import CustomJSONProvider

mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    app.json = CustomJSONProvider(app)

    app.config["MONGO_URI"] = os.getenv("MONGO_URI")

    # JWT 기본 설정
    app.config['JWT_SECRET_KEY'] = 'jungle09_secret_key'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=30)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=14)
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    jwt = JWTManager(app)

    app.config['JWT_COOKIE_SECURE'] = False # 로컬 테스트용 (나중에 HTTPS 배포 시 True로 변경)
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False # 로컬 테스트 시 CSRF 에러 방지

    mongo.init_app(app)

    from .routes import main
    from .routes import user
    from .routes import gonggu
    from .routes import auth
    app.register_blueprint(main.bp)
    app.register_blueprint(user.bp, url_prefix='/api/users')
    app.register_blueprint(gonggu.bp, url_prefix='/api/gonggu')
    app.register_blueprint(auth.bp, url_prefix='/api/auth')

    return app