from datetime import datetime

from bson.objectid import ObjectId
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

@bp.route('/list', methods=['GET'])
def get_gonggu_list():
    """
    공구 리스트 조회 API
    """
    cursor = None
    serialized_cursor = []
    limit=22 # 22개씩 조회, 22개면 다음 페이지 존재, 21개면 다음 페이지 없음

    try:
        last_id = request.args.get('last_id', default=None, type=str) # ObjectId 기준 페이징을 위한 값
        last_value = request.args.get('last_value', default=None) # 마감일 기준 페이징을 위한 값
        status = request.args.get('status', default=None, type=str) # 공구 상태 필터링을 위한 값
        sort_by = request.args.get('sort_by', default="latest", type=str) # 정렬 기준 (latest, deadline)

        if last_id in (None, "", "undefined"):
            last_id = None
        if last_value in (None, "", "undefined"):
            last_value = None

        if last_id and not ObjectId.is_valid(last_id):
            return jsonify({"error": "Invalid last_id"}), 400

        # 기본 필터 조건
        query = {}
        if status: # status 값이 존재하면 query에 status 조건 추가
            query['status'] = status

        if sort_by == 'latest': # 최신순 정렬
            if last_id:
                query['_id'] = {"$lt": ObjectId(last_id)}

            cursor = list(mongo.db.gonggu.find(query).sort("_id", -1).limit(limit))

        elif sort_by == 'deadline':
            today = datetime.now().strftime("%Y-%m-%d")
            last_deadline = (last_value or "")[:10]  # "2026-08-26T12:00:00"여도 날짜만

            if last_id and last_deadline:
                query["$or"] = [
                    {"deadline": {"$gt": last_deadline}},
                    {"deadline": last_deadline, "_id": {"$gt": ObjectId(last_id)}},
                ]
            else:
                query["deadline"] = {"$gte": today}

            cursor = list(
                mongo.db.gonggu.find(query)
                .sort([("deadline", 1), ("_id", 1)])
                .limit(limit)
            )

        serialized_cursor = []

        for data in cursor or []:
            item = {**data, "_id": ObjectId(data["_id"]).__str__()} # ObjectId를 문자열로 변환
            deadline = item.get("deadline") # 마감일을 isoformat으로 변환
            if hasattr(deadline, "isoformat"): # datetime 객체인지 확인
                item["deadline"] = deadline.isoformat() # datetime 객체를 isoformat 문자열로 변환
            item["id"] = item.get("gonggu_id") or item["_id"]
            serialized_cursor.append(item)

        return jsonify({"gonggu_list": serialized_cursor})

    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while fetching gonggu list"}), 500



# TODO: 인기 글 조회 API
