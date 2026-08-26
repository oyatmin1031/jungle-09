from flask import Blueprint, render_template
from .. import mongo

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def home():
    # TODO: 로그인 여부 찾는 로직

    return render_template('index.html', username='username')

   
@bp.route('/gonggu/create', methods=['GET'])
def create_gonggu_page():
    return render_template('create_post.html')

@bp.route('/test')
def test():
    mongo.db.posts.insert_one({"title": "로컬에서 EC2로 연결 테스트"})
    titles = [p["title"] for p in mongo.db.posts.find()]
    return {"posts": titles}