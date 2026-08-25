from flask import Blueprint, jsonify, request
from .. import mongo

bp = Blueprint('gonggu', __name__, url_prefix='/api/gonggu')

@bp.route('/<gonggu_id>', methods=['GET'])
def find_gonggu(gonggu_id):
    """
    공구 검색 API
    """
    try:
        result = mongo.db.gonggu.find_one({"gonggu_id": gonggu_id}, {"_id":0})
        return jsonify({"gonggu": result})

    except Exception as e:
        print(e)
        return jsonify()

@bp.route('/gonggu/<last_gonggu_id>', methods=['GET'])
def get_gonggu_list(last_gonggu_id):
    """
    공구 리스트 조회 API
    """
    try:
        # last_gonggu_id 이후의 공구 리스트 조회
        result = list(mongo.db.gonggu.find({"gonggu_id": {"$gt": last_gonggu_id}}, {"_id":0}).sort("gonggu_id", 1).limit(10))
        return jsonify({"gonggu_list": result})

    except Exception as e:
        print(e)
        return jsonify()