import json
from webbrowser import get

from flask import Blueprint, Flask, Response, make_response
from flask_jwt_extended import get_jwt_identity
import time
from .. import mongo


bp = Blueprint('sse', __name__, url_prefix='/api/sse')


@bp.route('/stream', methods=['GET'])
def stream():
    user_id = get_jwt_identity()

    def event_stream():
        last_notif = None
        while True:
            # 랭킹
            # TODO: 신청수에 따른 sort
            ranking = list(mongo.db.gonggu.find(
                {"status": "recruiting"},
                {"_id": 1, "title": 1}
            ).limit(5))
            yield f"event:ranking\ndata: {ranking}\n\n"

            # if user_id:
                # 알림
                # notifs = list(mongo.db.gonggu.find(
                #     { $or: [
                #         {"user_id": user_id, "_id": {&gt: last_notif}},
                #         {"user_id": user_id, "_"}
                #     ]}
                # ))
                # json_data = json.dumps({"user_id": user_id})

                # yield f"event:notification\ndata: {notifs}\n\n"

            time.sleep(5)

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
