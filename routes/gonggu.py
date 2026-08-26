from datetime import datetime

from bson.objectid import ObjectId
from flask import Blueprint, jsonify, request
import requests
from bs4 import BeautifulSoup
from .. import mongo
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

bp = Blueprint('gonggu', __name__, url_prefix='/api/gonggu')

@bp.route('/<gonggu_id>', methods=['GET'])
def find_gonggu(gonggu_id):
    """
    공구 검색 API
    """
    try:
        result = mongo.db.gonggu.find_one( {"_id": ObjectId(gonggu_id)})
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
    
def get_product_image(product_link): 
    try:
        response = requests.get(product_link)
        print("TEST_PRODUCT_RESPONSE =", response.status_code)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        image_meta = soup.find(
            "meta",
            attrs={"property": "og:image"}
        )
        
        print("찾은 이미지 태그:", image_meta)
        
        if image_meta:
            image_url = image_meta.get("content")
        else:
            image_url = "/static/images/default_product.png"
            
    except Exception as e:
        print("이미지 불러오기 실패:", e)
        image_url = "/static/images/default_product.png"
    
    return image_url

@bp.route('/', methods=['POST'])
@jwt_required()
def create_gonggu():
    """
    공구 생성 API
    """
    # 1. 로그인한 사용자 확인
    username = get_jwt_identity()
    user = mongo.db.users.find_one({'username': username})
    nickname = user["nickname"]
    
    # 2. 폼 데이터 받기
    title=request.form.get('title')
    product_name=request.form.get('product_name')
    category=request.form.get('category')
    deadline=request.form.get('deadline')
    max_quantity=int(request.form.get('max_quantity'))
    unit_amount=int(request.form.get('unit_amount'))
    unit_type=request.form.get('unit_type')
    unit_price=int(request.form.get('unit_price'))
    product_link=request.form.get('product_link')
    image_url=get_product_image(product_link)
    kakao_link=request.form.get('kakao_link')
    description=request.form.get('description')
    status='recruiting'

    
    # 3. 게시글 딕셔너리 만들기
    gonggu_data = {
        "author_username": username,
        "author_nickname": nickname,
        "title": title,
        "product_name": product_name,
        "category": category,
        "deadline": deadline,
        "max_quantity": max_quantity,
        "unit_amount": unit_amount,
        "unit_type": unit_type,
        "unit_price": unit_price,
        "product_link": product_link,
        "kakao_link": kakao_link,
        "description": description,
        "image_url": image_url,
        "status": status
    }
    
    # 4. MongoDB에 insert
    result = mongo.db.gonggu.insert_one(gonggu_data)
    print(gonggu_data)
    
    # 5. MongoDB가 생성한 _id를 응답으로 반환
    return jsonify({
        "message":"공구 개설 성공"
    })
    



# 공구 참여
@bp.route('/<gonggu_id>/participants', methods=['POST'])
@jwt_required()
def participate_gonggu(gonggu_id):
    """
    공구 참여 API
    """
    try:
        current_user = get_jwt_identity() # 로그인한 유저 아이디 (신청자 id)
        data = request.json
        quantity = data.get('quantity', 1) # 프론트에서 보낸 수량 (기본값 1)

        participant_data = {
            "gonggu_id": gonggu_id,
            "username": current_user,
            "quantity": quantity
        }
        
        # participants 테이블에 넣기
        mongo.db.participants.insert_one(participant_data)        
        return jsonify({"message": "공구 신청이 완료되었습니다!"}), 201

    except Exception as e:
        print(f"참여 에러: {e}")
        return jsonify({"message": "서버 에러가 발생했습니다."}), 500

# TODO: 인기 글 조회 API
