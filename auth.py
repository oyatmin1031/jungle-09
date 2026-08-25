from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    set_refresh_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash

# 이 아래 라우트들은 전부 /api/auth 로 시작함
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 회원가입
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    nickname = data.get('nickname')
    
    # 1. DB에서 username 중복 검사
    
    # 2. 비밀번호 암호화
    hashed_password = generate_password_hash(password)
    
    # 3. DB에 유저 정보 저장 (db.users.insert_one)

    return jsonify({"msg": "회원가입 성공"}), 201