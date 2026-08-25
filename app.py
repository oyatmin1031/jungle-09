from flask import Flask
import os
# MongoDB 관련 모듈 임포트
from pymongo import MongoClient
from dotenv import load_dotenv

# JWT 관련 모듈 임포트
from flask_jwt_extended import JWTManager
import datetime

# MongoDB 연결
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

app = Flask(__name__)

# JWT 기본 설정
app.config['JWT_SECRET_KEY'] = 'jungle09_secret_key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=30)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=14)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
jwt = JWTManager(app)

app.config['JWT_COOKIE_SECURE'] = False # 로컬 테스트용 (나중에 HTTPS 배포 시 True로 변경)
app.config['JWT_COOKIE_CSRF_PROTECT'] = False # 로컬 테스트 시 CSRF 에러 방지

# 블루프린트 등록 (bp는 DB 설정 이후에 해야 함!!)
from auth import auth_bp  # 회원관리용 bp 가져오기
app.register_blueprint(auth_bp)


@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/test')
def test():
    db.posts.insert_one({"title": "로컬에서 EC2로 연결 테스트"})
    titles = [p["title"] for p in db.posts.find()]
    return {"posts": titles}

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)