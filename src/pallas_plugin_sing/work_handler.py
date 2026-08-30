from __future__ import annotations

from pallas.api.runtime import DirectBotAction, DirectWorkResult

from .submission import ACCEPTED_REPLY, RequestSongSubmission, SingSubmission, submit_request_song, submit_sing


def _failure_action(payload: dict, message: str) -> DirectWorkResult | None:
    if message == ACCEPTED_REPLY:
        return None
    return DirectWorkResult(
        actions=(
            DirectBotAction(
                action="send_group_msg",
                target_bot_id=int(payload["bot_id"]),
                payload={"group_id": int(payload["group_id"]), "message_text": message},
            ),
        )
    )


async def handle_sing_submit(payload: dict) -> DirectWorkResult | None:
    message = await submit_sing(
        SingSubmission(
            bot_id=int(payload["bot_id"]),
            group_id=int(payload["group_id"]),
            user_id=int(payload["user_id"]),
            speaker=str(payload["speaker"]),
            song_query=str(payload["song_query"]),
            key=payload.get("key", 0),
            chunk_index=int(payload.get("chunk_index", 0)),
            request_id=str(payload["request_id"]),
            message_id=int(payload.get("message_id") or 0),
        )
    )
    return _failure_action(payload, message)


async def handle_request_song(payload: dict) -> DirectWorkResult | None:
    message = await submit_request_song(
        RequestSongSubmission(
            bot_id=int(payload["bot_id"]),
            group_id=int(payload["group_id"]),
            user_id=int(payload["user_id"]),
            song_name=str(payload["song_name"]),
            request_id=str(payload["request_id"]),
            message_id=int(payload.get("message_id") or 0),
        )
    )
    if message is None:
        return None
    return _failure_action(payload, message)


def work_handlers():
    return {
        "sing.submit": handle_sing_submit,
        "sing.request_song": handle_request_song,
    }
