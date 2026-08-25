from flask import Blueprint, jsonify, request,render_template
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
    
@bp.route('/create', methods=['GET'])
def create_gonggu_page():
    return render_template('create_post.html')    
    
@bp.route('/', methods=['POST'])
def create_gonggu():
    """
    공구 생성 API
    """
    # 1. 폼 데이터 받기
    title=request.form.get('title')
    category=request.form.get('category')
    deadline=request.form.get('deadline')
    max_quantity=request.form.get('max_quantity')
    unit_amount=request.form.get('unit_amount')
    unit_type=request.form.get('unit_type')
    unit_price=request.form.get('unit_price')
    product_link=request.form.get('product_link')
    kakao_link=request.form.get('kakao_link')
    description=request.form.get('description')
    
    # 2. 게시글 딕셔너리 만들기
    gonggu_data = {
        "title": title,
        "category": category,
        "deadline": deadline,
        "max_quantity": max_quantity,
        "unit_amount": unit_amount,
        "unit_type": unit_type,
        "unit_price": unit_price,
        "product_link": product_link,
        "kakao_link": kakao_link,
        "description": description
    }
    
    # 3. MongoDB에 insert
    result = mongo.db.gonggu.insert_one(gonggu_data)
    
    # 4. MongoDB가 생성한 _id를 응답으로 반환
    return jsonify({
        "message":"공구 개설 성공"
    })