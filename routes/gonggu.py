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



## 공구 관리 페이지
# 내가 참여한 공구 리스트 조회
@bp.route('/my_gonggu', methods=['GET'])
def get_my_gonggu_list():  
    """
    내가 참여한 공구 리스트 조회 API
    """
    # 게시글 제목, 수량, 마감일, 오픈채팅 링크, 공구 상태 불러오기
    try:
        current_user = get_jwt_identity() # 로그인한 유저 아이디

        # 내가 참여한 내역(ID와 수량) 가져오기
        participations = list(mongo.db.participants.find(
            {"username": current_user}, 
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
            {"gonggu_id": {"$in": gonggu_ids}}, 
            {"_id": 0}
        ))

        # 최종 리스트 (제목, 수량, 마감일, 오픈채팅 링크, 공구 상태)
        result = []
        for gonggu in gonggu_list:
            g_id = gonggu.get("gonggu_id")
            
            item = {
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
def get_my_created_gonggu_list():  
    """
    내가 개설한 공구 리스트 조회 API
    """
    try:
        current_user = get_jwt_identity() # 로그인한 유저 아이디
        # 내가 개설한 공구 리스트 조회
        result = list(mongo.db.gonggu.find({"username": current_user}, {"_id":0}))
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
        current_user = get_jwt_identity()
        data = request.json
        new_status = data.get('status')

        # 데이터베이스 업데이트 (해당 공구의 작성자가 본인일 때만 수정되도록 조건 추가)
        # 만약 작성자 아이디 저장 키값이 "author_username"이 아니라면 본인 코드에 맞게 수정해주세요.
        result = mongo.db.gonggu.update_one(
            {"gonggu_id": gonggu_id, "username": current_user}, 
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