from flask import Blueprint, jsonify, request
from app import mongo 

bp = Blueprint('main', __name__, prefix='/api/users')

@bp.route('/<user_id>', methods=['GET'])
def find_user(user_id):
    """
    유저 검색 API
    """
    try:
        result = mongo.db.users.find_one({}, {"_id":0})
        return jsonify({"user": result})

    except Exception as e:
        print(e)
        return jsonify()