from flask import Blueprint, render_template
from flask_jwt_extended import get_jwt_identity, jwt_required
from .. import mongo

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
@jwt_required(optional=True)
def home():

    user_id = get_jwt_identity()
    print(f"user_id: {user_id}")
    user = mongo.db.users.find_one({'_id': user_id}) if user_id else None
    return render_template('index.html', nickname=user.get('nickname') if user else None)

   
@bp.route('/gonggu/create', methods=['GET'])
def create_gonggu_page():
    return render_template('create_post.html')

@bp.route('/login')
def login():
    return render_template('login.html')

@bp.route('/register')
def register():
    return render_template('register.html')

@bp.route('/test')
def test():
    mongo.db.posts.insert_one({"title": "로컬에서 EC2로 연결 테스트"})
    titles = [p["title"] for p in mongo.db.posts.find()]
    return {"posts": titles}
