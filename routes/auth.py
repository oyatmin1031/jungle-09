from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    set_refresh_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity
)
from flask_jwt_extended.utils import set_access_cookies
from requests import auth
from werkzeug.security import generate_password_hash, check_password_hash
from .. import mongo

# 이 아래 라우트들은 전부 /api/auth 로 시작함
bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 회원가입
@bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    nickname = data.get('nickname')

    # 1. DB에서 username 중복 검사
    if mongo.db.users.find_one({'username': username}):
        return jsonify({'msg': '이미 존재하는 ID입니다'}), 409

    # 2. 비밀번호 암호화
    hashed_password = generate_password_hash(password)

    # 3. DB에 유저 정보 저장
    mongo.db.users.insert_one({
        'username': username,
        'password': hashed_password,
        'nickname': nickname
    })

    return jsonify({'msg': "회원가입 성공"}), 201

# 로그인
@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 1. DB에서 username 조회
    user = mongo.db.users.find_one({'username': username})
    if not user:
        return jsonify({'msg': '존재하지 않는 ID입니다'}), 404

    # 2. 비밀번호 확인
    if not check_password_hash(user['password'], password):
        return jsonify({'msg': '비밀번호가 일치하지 않습니다'}), 401

    # 3. JWT 토큰 생성
    # identity를 username이 아니라 id로 설정하여, 토큰에서 유저를 식별할 때 username이 아닌 id를 사용
    # find 할 때 id로 찾기. str<->objectId 변환 주의~
    access_token = create_access_token(identity=str(user['_id']))
    refresh_token = create_refresh_token(identity=str(user['_id']))

    response = jsonify({
            'data': {
                'msg': '로그인 성공',
                'accessToken': access_token,
                'tokenType': 'Bearer',
                'expiresIn': 1800
            }
        })

    set_access_cookies(response, access_token)
    # Refresh Token을 쿠키에 설정 (보안상 HttpOnly로 설정, 자동으로 브라우저가 처리)
    set_refresh_cookies(response, refresh_token)
    return response, 200

# 재발급
@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # 리프레시 토큰 있는지 확인
def refresh():
    current_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_id)
    return jsonify({
        'data': {
            'accessToken': new_access_token,
            'tokenType': 'Bearer',
            'expiresIn': 1800
        }
    }), 200

# 로그아웃
@bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'msg': '로그아웃 성공'})
    unset_jwt_cookies(response)
    return response, 200
