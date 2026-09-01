from nonebot import get_driver, logger, on_message, on_notice
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent, GroupRecallNoticeEvent
from nonebot.exception import ActionFailed, FinishedException, NetworkError
from nonebot.plugin import PluginMetadata
from nonebot.rule import Rule
from nonebot.typing import T_State
from pallas.api.config import GroupConfig
from pallas.api.limits import is_command_cooldown_ready, refresh_command_cooldown
from pallas.api.logging import register_plugin_startup_ready
from pallas.api.metadata import (
    PLUGIN_EXTRA_VERSION,
    PLUGIN_HOMEPAGE,
    PLUGIN_MENU_TEMPLATE,
    SCENE_GROUP,
    SCENE_PRIVATE,
    join_usage,
    usage_line,
)
from pallas.api.perm import group_message_permission_for_command
from pallas.api.platform import llm_command_tool_row
from pallas.product.llm.knowledge.declare import knowledge_source_row

from .commands import matches_song_title, parse_play_request, parse_sing_request, parse_song_request
from .config import build_sing_command_prefixes, get_sing_config, sing_server_url, sync_sing_ingress_command_prefixes
from .ncm_login import get_song_id, get_song_title_with_artist
from .submission import (
    PlaySubmission,
    RequestSongSubmission,
    SingSubmission,
    cancel_pending_task_for_message,
    response_status_code,
    response_task_id,
    submit_play,
    submit_request_song,
    submit_sing,
)

__plugin_meta__ = PluginMetadata(
    name="牛牛唱歌",
    description="群内 AI 翻唱、点歌与续唱。",
    usage=join_usage(
        usage_line("牛牛唱歌 〈歌曲名〉 [key=±N]", "AI 翻唱，可调音调"),
        usage_line("牛牛继续唱 / 牛牛接着唱", "续唱上一首"),
        usage_line("牛牛点歌 〈歌曲名〉", "播放网易云原曲"),
        usage_line("牛牛什么歌 / 牛牛哪首歌 / 牛牛啥歌", "查询当前曲目"),
    ),
    type="application",
    homepage=PLUGIN_HOMEPAGE,
    supported_adapters={"~onebot.v11"},
    extra={
        "help_tag": "fun",
        "version": PLUGIN_EXTRA_VERSION,
        "menu_template": PLUGIN_MENU_TEMPLATE,
        "reload_policy": "metadata",
        "ingress_route": {"lane": "remote"},
        # 启动后由 sync_sing_ingress_command_prefixes 按 sing_speakers 覆盖前缀与帮助音色列表
        "command_prefixes": build_sing_command_prefixes({"帕拉斯": "pallas", "牛牛": "pallas"}),
        "command_permissions": [
            {
                "id": "sing.sing",
                "label": "牛牛唱歌 / 牛牛继续唱",
                "default": "everyone",
            },
            {"id": "sing.play", "label": "牛牛唱歌（随机）", "default": "everyone"},
            {"id": "sing.request_song", "label": "牛牛点歌", "default": "everyone"},
            {"id": "sing.song_title", "label": "牛牛什么歌", "default": "everyone"},
            {"id": "sing.ncm_login", "label": "网易云登录", "default": "superuser"},
            {"id": "sing.ncm_logout", "label": "网易云登出", "default": "superuser"},
        ],
        "command_limits": [
            {"id": "sing.sing", "cd_sec": 8},
            {"id": "sing.play", "cd_sec": 3},
            {"id": "sing.request_song", "cd_sec": 5},
            {"id": "sing.song_title", "cd_sec": 2},
            {"id": "sing.ncm_login", "cd_sec": 5},
            {"id": "sing.ncm_logout", "cd_sec": 5},
        ],
        "llm_tools": [
            llm_command_tool_row(
                name="sing.sing",
                command_id="sing.sing",
                description=(
                    "按歌名 AI 翻唱。用户明确给出歌名要求唱歌、唱一首、翻唱时使用；"
                    "禁止把「牛牛唱歌」「随机」「随便」等空命令当 song；"
                    "用户只发「牛牛唱歌」未点歌名时不要调用本工具（由随机播放命令处理）。"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "song": {
                            "type": "string",
                            "description": "歌曲名，尽量保留用户原话",
                        },
                    },
                    "required": ["song"],
                },
                command_template="牛牛唱歌 {song}",
                hints=["唱歌", "唱一首", "翻唱", "来一首", "来首歌", "音乐"],
            ),
            llm_command_tool_row(
                name="sing.continue",
                command_id="sing.sing",
                description="续唱上一首未完成的歌。用户说继续唱、接着唱时使用。",
                parameters={"type": "object", "properties": {}},
                command_template="牛牛继续唱",
                hints=["继续唱", "接着唱"],
            ),
            llm_command_tool_row(
                name="sing.request_song",
                command_id="sing.request_song",
                description=("点播网易云原曲。用户明确要求点歌、放歌、放首歌、听歌、播歌、牛牛音乐时使用。"),
                parameters={
                    "type": "object",
                    "properties": {
                        "song": {
                            "type": "string",
                            "description": "歌曲名，尽量保留用户原话",
                        },
                    },
                    "required": ["song"],
                },
                command_template="牛牛点歌 {song}",
                hints=[
                    "点歌",
                    "放歌",
                    "放首歌",
                    "放首",
                    "来首",
                    "听歌",
                    "播歌",
                    "播放歌曲",
                    "音乐",
                    "牛牛音乐",
                    "我想听",
                    "想听",
                    "听一下",
                    "来点音乐",
                    "想听歌",
                    "想听首",
                ],
            ),
            llm_command_tool_row(
                name="sing.song_title",
                command_id="sing.song_title",
                description="查询当前正在唱/播的歌名。用户问什么歌、哪首歌时使用。",
                parameters={"type": "object", "properties": {}},
                command_template="牛牛什么歌",
                hints=["什么歌", "哪首歌"],
            ),
        ],
        "menu_data": [
            {
                "func": "牛牛唱歌",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛唱歌 歌曲名 [key=±N]",
                "command_permission": "sing.sing",
                "brief_des": "AI 翻唱指定歌曲",
                "detail_des": "按歌名搜索并翻唱，可用 key=±N 调整音调；每次会返回一段音频。",
            },
            {
                "func": "继续唱",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛继续唱 / 牛牛接着唱",
                "command_permission": "sing.sing",
                "brief_des": "继续上次未完成的歌曲",
                "detail_des": "接着唱上一次没唱完的那首歌，继续返回下一段片段。",
            },
            {
                "func": "点歌",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛点歌 歌曲名",
                "command_permission": "sing.request_song",
                "brief_des": "播放网易云原曲",
                "detail_des": "按歌名搜索原曲并播放；如果登录状态可用，也能点需要会员权限的歌。",
            },
            {
                "func": "牛牛什么歌",
                "trigger_method": "on_message",
                "trigger_scene": SCENE_GROUP,
                "trigger_condition": "牛牛什么歌 / 牛牛哪首歌 / 牛牛啥歌",
                "command_permission": "sing.song_title",
                "brief_des": "查询当前播放的歌曲名",
                "detail_des": "查看牛牛当前正在唱的是哪一首歌。",
            },
            {
                "func": "网易云登录",
                "trigger_method": "on_cmd",
                "trigger_scene": SCENE_PRIVATE,
                "trigger_condition": "网易云登录 / 网易云登出",
                "command_permissions": ["sing.ncm_login", "sing.ncm_logout"],
                "brief_des": "绑定或解绑网易云",
                "detail_des": "私聊按提示完成登录或登出，用于点歌和播放需要网易云登录支持的内容。",
            },
        ],
        "knowledge_sources": [
            knowledge_source_row(
                source_id="sing.faq",
                title="牛牛唱歌说明",
                description="AI 翻唱、点歌与续唱",
                chunks=[
                    {
                        "title": "AI 翻唱",
                        "content": ("发送「牛牛唱歌 歌曲名」可 AI 翻唱；可选 key=±N 调整音调（-12 到 12）。"),
                        "keywords": "唱歌,翻唱,牛牛唱歌,key,音调",
                    },
                    {
                        "title": "续唱与点歌",
                        "content": (
                            "「牛牛继续唱 / 牛牛接着唱」续唱上一首；"
                            "「牛牛点歌 歌曲名」播放网易云原曲；"
                            "「牛牛什么歌 / 牛牛哪首歌 / 牛牛啥歌」查询当前曲目。"
                        ),
                        "keywords": "继续唱,接着唱,点歌,什么歌,原曲",
                    },
                    {
                        "title": "网易云登录",
                        "content": (
                            "私聊「网易云登录 / 网易云登出」可绑定或解绑网易云账号，"
                            "用于播放需登录支持的内容（维护者向口令）。"
                        ),
                        "keywords": "网易云,登录,登出,会员",
                    },
                    {
                        "title": "与口令工具的分工",
                        "content": (
                            "闲聊中若用户要唱歌或点歌，可调用 sing.sing / sing.request_song 等工具；"
                            "效果与「牛牛唱歌 / 牛牛点歌」一致，不要编造其它入口。"
                        ),
                        "keywords": "工具,口令,唱歌,点歌",
                    },
                ],
            ),
        ],
    },
)


async def safe_finish(matcher, message: str | None = None) -> None:
    """发送收尾文案；协议拒发时降级为 warning，仍正常结束 matcher。"""
    if message is not None:
        try:
            await matcher.send(message)
        except (ActionFailed, NetworkError) as err:
            logger.warning("sing reply send failed: {}", err)
    raise FinishedException


async def guard_command_cooldown(
    matcher,
    event: GroupMessageEvent,
    command_id: str,
    *,
    speak: bool = True,
) -> bool:
    if not await is_command_cooldown_ready(event, command_id):
        if speak:
            await safe_finish(matcher, "牛牛还在回味上一首，稍等再点歌吧。")
        return False
    await refresh_command_cooldown(event, command_id)
    return True


def sing_debug_enabled() -> bool:
    return bool(get_sing_config().sing_rule_debug)


def log_rule_skip(
    rule_name: str,
    event: GroupMessageEvent | Event,
    reason: str,
    text: str | None = None,
) -> None:
    if not sing_debug_enabled():
        return
    logger.debug(
        "sing rule skip rule={} bot_id={} group_id={} user_id={} text={!r} reason={}",
        rule_name,
        getattr(event, "self_id", ""),
        getattr(event, "group_id", 0),
        getattr(event, "user_id", 0),
        (text or "").strip(),
        reason,
    )


async def finish_on_cooldown(matcher, event: GroupMessageEvent, command_id: str) -> bool:
    return await guard_command_cooldown(matcher, event, command_id)


async def is_to_sing(event: GroupMessageEvent, state: T_State) -> bool:
    plugin_config = get_sing_config()
    if not plugin_config.sing_enable:
        log_rule_skip("sing", event, "sing disabled")
        return False
    text = event.get_plaintext()
    if not text:
        log_rule_skip("sing", event, "empty text")
        return False

    outcome = parse_sing_request(text, plugin_config.sing_speakers)
    command = outcome.value
    if command is None:
        log_rule_skip("sing", event, outcome.rejection or "unmatched command", text)
        return False
    state["speaker"] = command.speaker
    state["key"] = command.key

    if command.kind == "sing":
        state["song_id"] = command.song_query
        state["chunk_index"] = command.chunk_index
        return True

    if command.kind == "continue":
        progress = await GroupConfig(group_id=event.group_id).sing_progress()
        if not progress:
            log_rule_skip("sing", event, "continue without progress", text)
            return False
        logger.info(
            f"Bot [{event.self_id}] resumed continue progress in group [{event.group_id}]: "
            f"song [{progress.song_id}] at chunk [{progress.chunk_index}]"
        )

        song_id = str(progress.song_id)
        chunk_index = progress.chunk_index + 1
        key_val = progress.key
        if not song_id or chunk_index > 100:
            log_rule_skip(
                "sing",
                event,
                f"invalid continue progress song_id={song_id} chunk_index={chunk_index}",
                text,
            )
            return False
        state["song_id"] = song_id
        state["chunk_index"] = chunk_index
        state["key"] = key_val
        return True

    return False


sing_msg = on_message(
    rule=Rule(is_to_sing),
    priority=5,
    block=True,
    permission=group_message_permission_for_command("sing.sing"),
)


@sing_msg.handle()
async def handle_sing(bot: Bot, event: GroupMessageEvent, state: T_State):
    if not await finish_on_cooldown(sing_msg, event, "sing.sing"):
        return
    message = await submit_sing(
        SingSubmission(
            bot_id=int(bot.self_id),
            group_id=event.group_id,
            user_id=event.user_id,
            speaker=state["speaker"],
            song_query=state["song_id"],
            key=state["key"],
            chunk_index=state["chunk_index"],
            message_id=int(event.message_id),
        )
    )
    await safe_finish(sing_msg, message)


async def is_play(bot: Bot, event: Event, state: T_State) -> bool:
    plugin_config = get_sing_config()
    text = event.get_plaintext()
    command = parse_play_request(text or "", plugin_config.sing_speakers)
    if command is None:
        log_rule_skip("play", event, "not bare prefix+唱歌", text)
        return False
    state["speaker"] = command.speaker
    return True


play_cmd = on_message(
    rule=Rule(is_play),
    permission=group_message_permission_for_command("sing.play"),
    priority=5,
    # 命中随机播放后挡住闲聊，避免 LLM 再调 sing.sing 二次投递
    block=True,
)


@play_cmd.handle()
async def handle_play(bot: Bot, event: GroupMessageEvent, state: T_State):
    if not await finish_on_cooldown(play_cmd, event, "sing.play"):
        return
    message = await submit_play(
        PlaySubmission(
            bot_id=int(bot.self_id),
            group_id=event.group_id,
            user_id=event.user_id,
            speaker=state["speaker"],
            message_id=int(event.message_id),
        )
    )
    await safe_finish(play_cmd, message)


async def is_to_request_song(event: GroupMessageEvent, state: T_State) -> bool:
    plugin_config = get_sing_config()
    if not plugin_config.sing_enable:
        log_rule_skip("request", event, "sing disabled")
        return False
    text = event.get_plaintext()
    if not text:
        log_rule_skip("request", event, "empty text")
        return False

    outcome = parse_song_request(text, plugin_config.sing_speakers)
    command = outcome.value
    if command is None:
        log_rule_skip("request", event, outcome.rejection or "request pattern not matched", text)
        return False
    state["speaker"] = command.speaker
    state["song_name"] = command.song_name
    return True


request_song_msg = on_message(
    rule=Rule(is_to_request_song),
    priority=5,
    block=True,
    permission=group_message_permission_for_command("sing.request_song"),
)


@request_song_msg.handle()
async def handle_request_song(bot: Bot, event: GroupMessageEvent, state: T_State):
    if not await finish_on_cooldown(request_song_msg, event, "sing.request_song"):
        return
    message = await submit_request_song(
        RequestSongSubmission(
            bot_id=int(bot.self_id),
            group_id=event.group_id,
            user_id=event.user_id,
            song_name=state["song_name"],
            message_id=int(event.message_id),
        )
    )
    if message is not None:
        await safe_finish(request_song_msg, message)


async def what_song(event: Event) -> bool:
    text = event.get_plaintext()
    return matches_song_title(text, get_sing_config().sing_speakers)


async def is_sing_recall(event: Event) -> bool:
    return isinstance(event, GroupRecallNoticeEvent)


song_title_cmd = on_message(
    rule=Rule(what_song),
    priority=12,
    block=True,
    permission=group_message_permission_for_command("sing.song_title"),
)


@song_title_cmd.handle()
async def _(event: GroupMessageEvent):
    config = GroupConfig(event.group_id)
    progress = await config.sing_progress()
    if not progress:
        return
    logger.info(
        f"Bot [{event.self_id}] answered song title query in group [{event.group_id}]: song [{progress.song_id}]"
    )
    if not await guard_command_cooldown(song_title_cmd, event, "sing.song_title", speak=False):
        return
    song_detail = await get_song_title_with_artist(progress.song_id)
    if not song_detail:
        return
    song_title, artists = song_detail
    reply = f"{song_title} - {' / '.join(artists)}" if artists else song_title
    await safe_finish(song_title_cmd, reply)


# 按当前音频映射展开 ingress 前缀（否则自定义前缀进不了唱歌 matcher）
sync_sing_ingress_command_prefixes(get_sing_config().sing_speakers, meta=__plugin_meta__)

# 在 matcher 与元数据初始化完成后登记 direct 路由；旧版 Bot 继续使用 matcher。
try:
    from . import direct as direct  # noqa: E402, F401
except ModuleNotFoundError as exc:
    if exc.name != "pallas.api.runtime":
        raise

# 登记 AI callback 投递收尾（需 Bot 侧 runner 调用 invoke_media_task_success）。
from . import media_callback as _sing_media_callback  # noqa: E402

# 用户撤回点歌/唱歌消息时取消未开始的投递，避免撤回后仍收到歌曲
sing_recall_notice = on_notice(
    rule=Rule(is_sing_recall),
    priority=13,
    block=False,
)


@sing_recall_notice.handle()
async def handle_sing_recall(event: GroupRecallNoticeEvent):
    if await cancel_pending_task_for_message(int(event.group_id), int(event.message_id)):
        logger.info(
            f"Bot [{event.self_id}] cancelled pending sing task for recalled message [{event.message_id}] "
            f"in group [{event.group_id}]"
        )


@get_driver().on_startup
async def _sing_ready() -> None:
    register_plugin_startup_ready("sing", detail="唱歌命令与媒体任务钩子注册完成")
