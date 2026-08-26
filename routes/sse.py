import json
from webbrowser import get

from flask import Blueprint, Flask, Response, make_response
from flask_jwt_extended import get_jwt_identity
import time
from .. import mongo

bp = Blueprint('sse', __name__, url_prefix='/api/sse')

# def generate_sse(user_id):
#     """
#     SSE 이벤트 생성기
#     """
#     while True:

#         data =
#         yield f"event: notice\ndata: {}\n\n"
#         time.sleep(5)



@bp.route('/stream', methods=['GET'])
def stream():
    # user_id = get_jwt_identity()
    user_id = "test"

    def event_stream():
        while True:
            data = json.dumps({"user_id": user_id})

            yield f"event:notification\ndata: {data}\n\n"

            time.sleep(2)
    return Response(
        response= event_stream(),
        mimetype='text/event-stream',
        headers= {
            'Content-Type': 'text/event-steam',
            'Cache-Control':'no-cache',
            'Connection': 'keep-alive',
            'S': 'no'
        }
    )

# TODO: 상태 변경 시 알림 전송
# TODO: 작성자의 경우 타인이 참여시 알림 전송
# TODO: 참여자가 취소 시 알림 전송
# TODO: 모든 참여자가 모이면 알림 전송
# 연결은 한번.
