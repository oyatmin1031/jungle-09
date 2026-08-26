import json
import time
from webbrowser import get

from flask import Blueprint, Flask, Response, make_response
from flask_jwt_extended import get_jwt_identity

from .. import mongo

bp = Blueprint("sse", __name__, url_prefix="/api/sse")


@bp.route("/stream", methods=["GET"])
def stream():
    user_id = get_jwt_identity()

    def event_stream():
        last_rank = None # 랭킹이 바뀌었는지 확인하기 위한 변수
        last_notif = None # 마지막으로 전송한 알림의 _id를 저장하기 위한 변수
        while True:
            ranking = list(
                mongo.db.gonggu.find(
                    {"status": "recruiting"},
                    {
                        "_id": 1,
                        "gonggu_id": 1,
                        "title": 1,
                        "image_url": 1,
                        "join_count": 1,
                    },
                )
                .sort("current_quantity", -1)
                .limit(5)
            )

            # 랭킹이 바뀌었을 때만 전송
            if ranking != last_rank:
                last_rank = ranking
                yield f"event: ranking\ndata: {json.dumps(ranking, default=str)}\n\n"

            if user_id:
                notifs = list(
                    mongo.db.notifications.find(
                        {
                            "user_id": user_id,
                            "_id": {"$gt": last_notif}
                            if last_notif
                            else {"$exists": True},
                        }
                    )
                    .sort("_id", 1)
                    .limit(20)
                )
                for n in notifs:
                    last_notif = n["_id"]
                    n["_id"] = str(n["_id"])
                    yield f"event: notification\ndata: {json.dumps(n, default=str)}\n\n"

            yield ": ping\n\n"
            time.sleep(5)

    # def event_stream():
    #     last_notif = None
    #     while True:
    #         # 랭킹
    #         # TODO: 신청수에 따른 sort
    #         ranking = list(
    #             mongo.db.gonggu.find(
    #                 {"status": "recruiting"}, {"_id": 1, "title": 1}
    #             ).limit(5)
    #         )
    #         yield f"event:ranking\ndata: {ranking}\n\n"

    #         # if user_id:
    #         # 알림
    #         # notifs = list(mongo.db.gonggu.find(
    #         #     { $or: [
    #         #         {"user_id": user_id, "_id": {&gt: last_notif}},
    #         #         {"user_id": user_id, "_"}
    #         #     ]}
    #         # ))
    #         # json_data = json.dumps({"user_id": user_id})

    #         # yield f"event:notification\ndata: {notifs}\n\n"

    #         time.sleep(5)

    return Response(
        response=event_stream(),
        mimetype="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# TODO: 상태 변경 시 알림 전송
# TODO: 작성자의 경우 타인이 참여시 알림 전송
# TODO: 참여자가 취소 시 알림 전송
# TODO: 모든 참여자가 모이면 알림 전송
