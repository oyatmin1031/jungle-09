from flask import Blueprint, jsonify, request
from app import mongo

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