from __future__ import annotations

from pallas.api.config import GroupConfig
from pallas.api.limits import is_command_cooldown_ready, refresh_command_cooldown
from pallas.api.runtime import (
    DirectCommandContext,
    DirectCommandResult,
    DirectReply,
    DirectWorkJob,
    completion_effect,
    matcher_fallback,
    register_prefix_command_handler,
)
from ulid import ULID

from .commands import parse_sing_request, parse_song_request
from .config import get_sing_config
from .submission import ACCEPTED_REPLY


def command_prefixes(suffixes: tuple[str, ...]) -> tuple[str, ...]:
    prefixes: list[str] = []
    for speaker in get_sing_config().sing_speakers:
        head = str(speaker or "").strip()
        if head:
            prefixes.extend(f"{head}{suffix}" for suffix in suffixes)
    return tuple(dict.fromkeys(prefixes))


async def sing(context: DirectCommandContext) -> DirectCommandResult:
    config = get_sing_config()
    if not config.sing_enable:
        return matcher_fallback("disabled")
    outcome = parse_sing_request(context.command_text, config.sing_speakers)
    command = outcome.value
    if command is None:
        reason = "play_command" if outcome.rejection == "endswith sing cmd -> play path" else "invalid_command"
        return matcher_fallback(reason)
    if command.kind == "continue":
        progress = await GroupConfig(context.group_id).sing_progress()
        if not progress:
            return matcher_fallback("continue_without_progress")
        song_id = str(progress.song_id)
        chunk_index = progress.chunk_index + 1
        if not song_id or chunk_index > 100:
            return matcher_fallback("invalid_continue_progress")
        song_query = song_id
        key = progress.key
    else:
        song_query = str(command.song_query or "")
        chunk_index = command.chunk_index
        key = command.key
    if not await is_command_cooldown_ready(context.event, "sing.sing"):
        return matcher_fallback("cooldown")
    request_id = str(ULID())
    job = DirectWorkJob(
        kind="sing.submit",
        payload={
            "request_id": request_id,
            "bot_id": context.bot_id,
            "group_id": context.group_id,
            "user_id": int(context.event.user_id),
            "speaker": command.speaker,
            "song_query": song_query,
            "key": key,
            "chunk_index": chunk_index,
            "message_id": context.message_id,
        },
        idempotency_key=f"sing:{context.bot_id}:{context.group_id}:{context.message_id}",
    )

    async def refresh_cooldown() -> None:
        await refresh_command_cooldown(context.event, "sing.sing")

    return DirectCommandResult(
        replies=(DirectReply(ACCEPTED_REPLY),),
        work_jobs=(job,),
        effects=(completion_effect("sing.sing.cooldown", refresh_cooldown),),
    )


async def request_song(context: DirectCommandContext) -> DirectCommandResult:
    config = get_sing_config()
    if not config.sing_enable:
        return matcher_fallback("disabled")
    outcome = parse_song_request(context.command_text, config.sing_speakers)
    command = outcome.value
    if command is None:
        return matcher_fallback("invalid_command")
    if not await is_command_cooldown_ready(context.event, "sing.request_song"):
        return matcher_fallback("cooldown")
    request_id = str(ULID())
    job = DirectWorkJob(
        kind="sing.request_song",
        payload={
            "request_id": request_id,
            "bot_id": context.bot_id,
            "group_id": context.group_id,
            "user_id": int(context.event.user_id),
            "song_name": command.song_name,
            "message_id": context.message_id,
        },
        idempotency_key=f"sing.request_song:{context.bot_id}:{context.group_id}:{context.message_id}",
    )

    async def refresh_cooldown() -> None:
        await refresh_command_cooldown(context.event, "sing.request_song")

    return DirectCommandResult(
        replies=(DirectReply(ACCEPTED_REPLY),),
        work_jobs=(job,),
        effects=(completion_effect("sing.request_song.cooldown", refresh_cooldown),),
    )


SING_DECLARATION = register_prefix_command_handler(
    handler_id="sing.sing.direct",
    module="sing",
    prefixes=command_prefixes(("唱歌", "继续唱", "接着唱")),
    command_id="sing.sing",
    execute=sing,
)
REQUEST_SONG_DECLARATION = register_prefix_command_handler(
    handler_id="sing.request_song.direct",
    module="sing",
    prefixes=command_prefixes(("点歌",)),
    command_id="sing.request_song",
    execute=request_song,
)
