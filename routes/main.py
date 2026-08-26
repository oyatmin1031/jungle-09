from flask import Blueprint, render_template
from flask_jwt_extended import get_jwt_identity, jwt_required
from .. import mongo
from bson import ObjectId

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
@jwt_required(optional=True)
def home():
    user_id = get_jwt_identity()
    print("user_id:", user_id)
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)}) if user_id else None
    write_gonggu = list(mongo.db.gonggu.find({"author_id": user_id})) if user_id else None
    print("write_gonggu:", write_gonggu)
    # 렌더링 전에 유저 확인 후, 없으면 none
    nickname = user.get('nickname') if user else None
    # 렌더링
    return render_template('index.html', nickname=nickname, write_gonggu=write_gonggu)

@bp.route('/gonggu/create', methods=['GET'])
def create_gonggu_page():
    return render_template('create_post.html')

@bp.route('/gonggu/<gonggu_id>')
def gonggu_detail_page(gonggu_id):
    gonggu = mongo.db.gonggu.find_one(
        {"_id": ObjectId(gonggu_id)}
    )

    return render_template(
    'detail_post.html',
    gonggu=gonggu,
    gonggu_id=gonggu_id
    )

@bp.route('/login')
def login():
    return render_template('login.html')

@bp.route('/register')
def register():
    return render_template('register.html')

@bp.route('/mypage')
def mypage():
    return render_template('mypage.html')

@bp.route('/test')
def test():
    mongo.db.posts.insert_one({"title": "로컬에서 EC2로 연결 테스트"})
    titles = [p["title"] for p in mongo.db.posts.find()]
    return {"posts": titles}
