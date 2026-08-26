from operator import is_

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

    # 작성한 공구 가져오기
    created_gonggu = list(mongo.db.gonggu.find({"author_id": user_id})) if user_id else None
    print("created_gonggu:", created_gonggu)

    # 참여한 공구 가져오기
    participated_gonggu = []
    if user_id:
        # participants 컬렉션에서 내 참여 내역 찾기
        participations = list(mongo.db.participants.find({"user_id": user_id}))
        if participations:
            # 참여 내역에서 공구 ID들만 뽑아내기
            gonggu_ids = [item["gonggu_id"] for item in participations]
            # 해당 ID를 가진 공구 글들을 찾아서 리스트로 만들기
            participated_gonggu = list(mongo.db.gonggu.find({"_id": {"$in": gonggu_ids}}))

    # 렌더링 전에 유저 확인 후, 없으면 none
    nickname = user.get('nickname') if user else None
    # 렌더링
    return render_template('index.html', nickname=nickname, created_gonggu=created_gonggu, participated_gonggu=participated_gonggu)

@bp.route('/gonggu/create', methods=['GET'])
def create_gonggu_page():
    return render_template('create_post.html')

@bp.route('/gonggu/<gonggu_id>')
@jwt_required(optional=True)
def gonggu_detail_page(gonggu_id):
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)}) if user_id else None
    nickname = user.get('nickname') if user else None

    is_author = mongo.db.gonggu.find_one({"_id": ObjectId(gonggu_id), "author_id": user_id}) is not None if user_id else False
    is_partisipant = mongo.db.participant.find_one({"gonggu_id": gonggu_id, "user_id": user_id}) is not None if user_id else False

    gonggu = mongo.db.gonggu.find_one(
        {"_id": ObjectId(gonggu_id)}
    )

    return render_template(
    'detail_post.html',
    nickname=nickname,
    is_author=is_author,
    is_partisipant=is_partisipant,
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
