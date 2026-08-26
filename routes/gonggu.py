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
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
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
        "author_id": user_id,
        "author_nickname": nickname,
        "title": title,
        "product_name": product_name,
        "category": category,
        "deadline": deadline,
        "max_quantity": max_quantity,
        "current_quantity": 0,
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
        current_id = get_jwt_identity() # 로그인한 유저 아이디 (신청자 id)
        data = request.json
        quantity = data.get('quantity', 1) # 프론트에서 보낸 수량 (기본값 1)
        gonggu = mongo.db.gonggu.find_one(
            {"_id": ObjectId(gonggu_id)}
        )
        if gonggu is None:
            return jsonify({
            "message": "존재하지 않는 공구입니다."
        }), 404
        if gonggu['author_id'] == current_id:
            return jsonify({
                "message": "본인이 개설한 공구에는 참여할 수 없습니다."
            }), 403
        if gonggu["status"] != "recruiting":
            return jsonify({
                "message": "현재 참여할 수 없는 공구입니다."
        }), 403
        existing_participant = mongo.db.participants.find_one({
            "gonggu_id": ObjectId(gonggu_id),
            "user_id": current_id
        })
        if existing_participant:
            return jsonify({
               "message": "이미 참여한 공구입니다."
            }), 400
            
        max_quantity = gonggu["max_quantity"]

        participant_data = {
            "gonggu_id": ObjectId(gonggu_id),
            "user_id": current_id,
            "quantity": quantity
        }
        result=mongo.db.gonggu.update_one(
            {
                "_id": ObjectId(gonggu_id),
                "current_quantity": {
                    "$lte": max_quantity - quantity
                }
            },
            {
                "$inc": {
                    "current_quantity": quantity
                }
            }
        )
        if result.modified_count == 0:
            return jsonify({
                "message": "남은 수량보다 많이 신청할 수 없습니다."
            }), 400
        # participants 테이블에 넣기
        mongo.db.participants.insert_one(participant_data)        
        return jsonify({"message": "공구 신청이 완료되었습니다!"}), 201

    except Exception as e:
        print(f"참여 에러: {e}")
        return jsonify({"message": "서버 에러가 발생했습니다."}), 500


# TODO: 인기 글 조회 API


## 공구 관리 페이지
# 내가 참여한 공구 리스트 조회
@bp.route('/my_gonggu', methods=['GET'])
@jwt_required()
def get_my_gonggu_list():  
    """
    내가 참여한 공구 리스트 조회 API
    """
    # 게시글 제목, 수량, 마감일, 오픈채팅 링크, 공구 상태 불러오기
    try:
        current_id = get_jwt_identity() # 로그인한 유저 아이디

        # 내가 참여한 내역(ID와 수량) 가져오기
        participations = list(mongo.db.participants.find(
            {"user_id": ObjectId(current_id)}, 
            {"gonggu_id": 1, "quantity": 1, "_id": 0}
        ))

        # 참여한 내역이 없으면 바로 빈 리스트 반환
        if not participations:
            return jsonify({"my_gonggu_list": []})

        # 참여한 내역을 딕셔너리로 변환
        quantity_map = {item["gonggu_id"]: item["quantity"] for item in participations}
        
        # 게시글 리스트 조회
        gonggu_ids = list(quantity_map.keys())
        gonggu_list = list(mongo.db.gonggu.find(
            {"_id": {"$in": gonggu_ids}}
        ))

        # 최종 리스트 (제목, 수량, 마감일, 오픈채팅 링크, 공구 상태)
        result = []
        for gonggu in gonggu_list:
            g_id = gonggu.get("_id")
            
            item = {
                "_id": str(g_id),
                "title": gonggu.get("title"),
                "quantity": quantity_map.get(g_id),
                "deadline": gonggu.get("deadline"),
                "kakao_link": gonggu.get("kakao_link"),
                "status": gonggu.get("status")
            }
            result.append(item)

        return jsonify({"my_gonggu_list": result}), 200

    except Exception as e:
        print(f"참여 내역 조회 에러: {e}")
        return jsonify({"message": "서버 에러가 발생했습니다."}), 500

# 내가 개설한 공구 리스트 조회
@bp.route('/my_created_gonggu', methods=['GET'])
@jwt_required()
def get_my_created_gonggu_list():  
    """
    내가 개설한 공구 리스트 조회 API
    """
    try:
        current_id = get_jwt_identity() # 로그인한 유저 아이디
        # 내가 개설한 공구 리스트 조회
        gonggu_list = list(mongo.db.gonggu.find({"author_id": current_id}))
        
        result = []
        for gonggu in gonggu_list:
            gonggu["_id"] = str(gonggu["_id"]) # ObjectId를 문자열로 변환
            result.append(gonggu)
            
        return jsonify({"my_created_gonggu_list": result})
    
    except Exception as e:
        print(e)
        return jsonify({"message": "서버 에러가 발생했습니다."}), 500

# 공구 진행 상태 변경
@bp.route('/<gonggu_id>/status', methods=['PATCH'])
@jwt_required()
def update_gonggu_status(gonggu_id):
    """
    공구 진행 상태 변경 API
    """
    try:
        current_id = get_jwt_identity()
        data = request.json
        new_status = data.get('status')

        # 데이터베이스 업데이트 (해당 공구의 작성자가 본인일 때만 수정되도록 조건 추가)
        result = mongo.db.gonggu.update_one(
            {"_id": ObjectId(gonggu_id), "author_id": current_id}, 
            {"$set": {"status": new_status}}
        )

        # 수정된 문서가 1개 이상이면 성공
        if result.modified_count > 0:
            return jsonify({"message": "상태가 성공적으로 변경되었습니다."}), 200
        else:
            return jsonify({"message": "상태 변경 권한이 없거나 이미 같은 상태입니다."}), 400

    except Exception as e:
        print(f"상태 변경 에러: {e}")
        return jsonify({"message": "서버 에러가 발생했습니다."}), 500