from flask import Blueprint, render_template
from app import mongo

bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def home():
    # TODO: 로그인 여부 찾는 로직
    return render_template('index.html', username='username')