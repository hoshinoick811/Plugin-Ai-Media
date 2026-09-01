from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _install_stub(name: str, module: types.ModuleType) -> None:
    sys.modules[name] = module


def _bootstrap_stub_modules() -> None:
    nonebot = types.ModuleType("nonebot")
    nonebot.logger = types.SimpleNamespace(
        info=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        debug=lambda *a, **k: None,
    )
    nonebot.get_driver = lambda: types.SimpleNamespace(on_startup=lambda fn: fn)
    nonebot.on_message = lambda *a, **k: types.SimpleNamespace(
        handle=lambda: (lambda fn: fn), finish=None, send=None
    )
    nonebot.on_notice = lambda *a, **k: types.SimpleNamespace(
        handle=lambda: (lambda fn: fn), finish=None, send=None
    )
    _install_stub("nonebot", nonebot)

    exception = types.ModuleType("nonebot.exception")

    class ActionFailed(Exception):
        pass

    class FinishedException(Exception):
        pass

    class NetworkError(Exception):
        pass

    exception.ActionFailed = ActionFailed
    exception.FinishedException = FinishedException
    exception.NetworkError = NetworkError
    _install_stub("nonebot.exception", exception)

    adapters = types.ModuleType("nonebot.adapters")
    adapters.Bot = object
    adapters.Event = object
    _install_stub("nonebot.adapters", adapters)

    ob11 = types.ModuleType("nonebot.adapters.onebot.v11")
    ob11.GroupMessageEvent = object
    ob11.GroupRecallNoticeEvent = object
    ob11.permission = types.SimpleNamespace(GROUP=object())
    _install_stub("nonebot.adapters.onebot.v11", ob11)

    plugin = types.ModuleType("nonebot.plugin")
    plugin.PluginMetadata = lambda **kwargs: kwargs
    _install_stub("nonebot.plugin", plugin)

    rule = types.ModuleType("nonebot.rule")
    rule.Rule = lambda fn: fn
    _install_stub("nonebot.rule", rule)

    typing_mod = types.ModuleType("nonebot.typing")
    typing_mod.T_State = dict
    _install_stub("nonebot.typing", typing_mod)

    ulid = types.ModuleType("ulid")
    ulid.ULID = lambda: "local-request-id"
    _install_stub("ulid", ulid)

    _install_stub("pallas", types.ModuleType("pallas"))
    _install_stub("pallas.api", types.ModuleType("pallas.api"))

    api_logging_mod = types.ModuleType("pallas.api.logging")
    api_logging_mod.format_plugin_event = lambda *args, **kwargs: " ".join(str(arg) for arg in args)
    api_logging_mod.register_plugin_startup_ready = lambda *a, **k: None
    _install_stub("pallas.api.logging", api_logging_mod)

    cmd_defaults = types.ModuleType("pallas.api.metadata")
    cmd_defaults.PLUGIN_EXTRA_VERSION = "4.0.1"
    cmd_defaults.PLUGIN_HOMEPAGE = "https://example.com"
    cmd_defaults.PLUGIN_MENU_TEMPLATE = "default"
    cmd_defaults.SCENE_GROUP = "group"
    cmd_defaults.SCENE_PRIVATE = "private"
    cmd_defaults.join_usage = lambda *lines: "\n".join(lines)
    cmd_defaults.usage_line = lambda text, desc: f"{text}: {desc}"
    _install_stub("pallas.api.metadata", cmd_defaults)

    config_mod = types.ModuleType("pallas.api.config")
    config_mod.GroupConfig = object
    config_mod.SingProgress = lambda **kwargs: types.SimpleNamespace(**kwargs)
    config_mod.TaskManager = types.SimpleNamespace(add_task=None, remove_task=None, get_task=None)
    _install_stub("pallas.api.config", config_mod)

    api_utils_mod = types.ModuleType("pallas.api.utils")
    api_utils_mod.HTTPXClient = types.SimpleNamespace(get=None, post=None)
    _install_stub("pallas.api.utils", api_utils_mod)

    limits_mod = types.ModuleType("pallas.api.limits")

    async def _cooldown_ready(*_a, **_k) -> bool:
        return True

    async def _refresh_cooldown(*_a, **_k) -> None:
        return None

    limits_mod.is_command_cooldown_ready = _cooldown_ready
    limits_mod.refresh_command_cooldown = _refresh_cooldown
    _install_stub("pallas.api.limits", limits_mod)

    perm_mod = types.ModuleType("pallas.api.perm")
    perm_mod.group_message_permission_for_command = lambda *_a, **_k: object()
    _install_stub("pallas.api.perm", perm_mod)

    platform_mod = types.ModuleType("pallas.api.platform")
    platform_mod.llm_command_tool_row = lambda **kwargs: kwargs
    platform_mod.SING_TASK_TYPES = frozenset({"sing", "play", "request"})
    platform_mod.register_media_task_hooks = lambda *a, **k: None
    _install_stub("pallas.api.platform", platform_mod)

    db_mod = types.ModuleType("pallas.core.foundation.db.modules")
    db_mod.SingProgress = lambda **kwargs: types.SimpleNamespace(**kwargs)
    _install_stub("pallas.core.foundation.db.modules", db_mod)

    utils_mod = types.ModuleType("pallas.core.shared.utils")
    utils_mod.HTTPXClient = types.SimpleNamespace(get=None, post=None)
    _install_stub("pallas.core.shared.utils", utils_mod)

    knowledge = types.ModuleType("pallas.product.llm.knowledge.declare")
    knowledge.knowledge_source_row = lambda **kwargs: kwargs
    _install_stub("pallas.product.llm.knowledge.declare", knowledge)
    _install_stub("pallas.product.llm.knowledge", types.ModuleType("pallas.product.llm.knowledge"))
    _install_stub("pallas.product.llm", types.ModuleType("pallas.product.llm"))
    _install_stub("pallas.product", types.ModuleType("pallas.product"))

    sing_config = types.ModuleType("pallas_plugin_sing.config")
    sing_config.get_sing_config = lambda: types.SimpleNamespace(
        sing_enable=True,
        sing_endpoint="/api/sing",
        play_endpoint="/api/play",
        request_endpoint="/api/request",
        sing_length=120,
        sing_speakers={"牛牛": "pallas"},
        sing_rule_debug=False,
    )
    sing_config.sing_server_url = lambda cfg=None: "http://127.0.0.1:9099"
    sing_config.build_sing_command_prefixes = lambda speakers: []
    sing_config.match_bare_play_speaker = lambda text, speakers: (
        "pallas" if (text or "").strip() == "牛牛唱歌" else None
    )
    sing_config.sync_sing_ingress_command_prefixes = lambda *a, **k: None
    _install_stub("pallas_plugin_sing.config", sing_config)

    ncm_login = types.ModuleType("pallas_plugin_sing.ncm_login")
    ncm_login.get_song_id = None
    ncm_login.get_song_title = None
    ncm_login.get_song_title_with_artist = None
    _install_stub("pallas_plugin_sing.ncm_login", ncm_login)


_bootstrap_stub_modules()

sing_mod = importlib.import_module("pallas_plugin_sing")  # noqa: E402
submission_mod = importlib.import_module("pallas_plugin_sing.submission")  # noqa: E402


class DummyMatcher:
    def __init__(self) -> None:
        self.finished: list[str] = []
        self.sent: list[str] = []

    async def send(self, message: str) -> None:
        self.sent.append(message)

    async def finish(self, message: str | None = None) -> None:
        if message is not None:
            self.finished.append(message)
        raise sing_mod.FinishedException


@pytest.mark.asyncio
async def test_safe_finish_swallows_action_failed() -> None:
    class RejectMatcher:
        async def send(self, _message: str) -> None:
            raise sing_mod.ActionFailed("send group message rejected: result=120")

    with pytest.raises(sing_mod.FinishedException):
        await sing_mod.safe_finish(RejectMatcher(), "欢呼吧！")


class DummyConfig:
    def __init__(self, group_id: int, cooldown: int = 10) -> None:
        self.group_id = group_id
        self.cooldown = cooldown
        self.updated_progress = None

    async def refresh_cooldown(self, _key: str) -> None:
        return None

    async def update_sing_progress(self, progress) -> None:
        self.updated_progress = progress


class DummyResponse:
    def __init__(self, task_id: str) -> None:
        self._task_id = task_id

    def json(self) -> dict[str, str]:
        return {"task_id": self._task_id}


def test_remote_task_id_does_not_replace_callback_request_id() -> None:
    payload = {
        "bot_id": "123456",
        "group_id": 42,
        "task_type": "sing",
        "start_time": 1000.0,
    }

    assert submission_mod.log_ignored_remote_task_id("local-request-id", "remote-task-id", payload) is None


@pytest.mark.asyncio
async def test_play_dispatch_uses_request_id_endpoint_and_keeps_request_id_task(monkeypatch: pytest.MonkeyPatch) -> None:
    added: list[tuple[str, dict]] = []
    removed: list[str] = []
    requests: list[tuple[str, dict]] = []
    matcher = DummyMatcher()

    class DummyBot:
        self_id = "123456"

    class DummyEvent:
        group_id = 42
        user_id = 7
        message_id = 555

    async def fake_add_task(task_id: str, payload: dict) -> None:
        added.append((task_id, dict(payload)))

    async def fake_remove_task(task_id: str) -> None:
        removed.append(task_id)

    async def fake_post(url: str, json: dict | None = None):
        requests.append((url, dict(json or {})))
        return DummyResponse("remote-play-task-id")

    async def fake_finish_on_cooldown(*_args, **_kwargs) -> bool:
        return True

    monkeypatch.setattr(sing_mod, "play_cmd", matcher)
    monkeypatch.setattr(submission_mod, "GroupConfig", DummyConfig)
    monkeypatch.setattr(submission_mod.TaskManager, "add_task", fake_add_task)
    monkeypatch.setattr(submission_mod.TaskManager, "remove_task", fake_remove_task)
    monkeypatch.setattr(submission_mod.HTTPXClient, "post", fake_post)
    monkeypatch.setattr(submission_mod, "ULID", lambda: "local-request-id")
    monkeypatch.setattr(sing_mod, "finish_on_cooldown", fake_finish_on_cooldown)

    with pytest.raises(sing_mod.FinishedException):
        await sing_mod.handle_play(DummyBot(), DummyEvent(), {"speaker": "pallas"})

    assert requests == [("http://127.0.0.1:9099/api/play/local-request-id", {"speaker": "pallas"})]
    assert removed == []
    assert [task_id for task_id, _ in added] == ["local-request-id"]
    assert added[0][1]["task_type"] == "play"
    assert matcher.sent == ["欢呼吧！"]


@pytest.mark.asyncio
async def test_request_song_updates_sing_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    added: list[tuple[str, dict]] = []
    calls: list[str] = []
    matcher = DummyMatcher()
    config = DummyConfig(42)

    class DummyBot:
        self_id = "123456"

    class DummyEvent:
        group_id = 42
        user_id = 7
        message_id = 555

    async def fake_add_task(task_id: str, payload: dict) -> None:
        calls.append("register")
        added.append((task_id, dict(payload)))

    async def fake_post(url: str, json: dict | None = None):
        calls.append("post")
        assert url.endswith("/api/request/local-request-id")
        assert json == {"song_id": 1474697449}
        return DummyResponse("remote-request-task-id")

    async def fake_finish_on_cooldown(*_args, **_kwargs) -> bool:
        return True

    async def fake_get_song_id(song_name: str):
        assert song_name == "随机"
        return 1474697449

    monkeypatch.setattr(sing_mod, "request_song_msg", matcher)
    monkeypatch.setattr(submission_mod, "GroupConfig", lambda group_id: config)
    monkeypatch.setattr(submission_mod.TaskManager, "add_task", fake_add_task)
    monkeypatch.setattr(submission_mod.HTTPXClient, "post", fake_post)
    monkeypatch.setattr(sing_mod, "finish_on_cooldown", fake_finish_on_cooldown)
    monkeypatch.setattr(submission_mod, "get_song_id", fake_get_song_id)
    monkeypatch.setattr(submission_mod, "ULID", lambda: "local-request-id")

    with pytest.raises(sing_mod.FinishedException):
        await sing_mod.handle_request_song(DummyBot(), DummyEvent(), {"song_name": "随机"})

    assert [task_id for task_id, _ in added] == ["local-request-id"]
    assert calls == ["register", "post"]
    assert added[0][1]["task_type"] == "request"
    assert config.updated_progress is not None
    assert config.updated_progress.song_id == "1474697449"
    assert config.updated_progress.chunk_index == 0
    assert config.updated_progress.key == 0
    assert matcher.sent == ["欢呼吧！"]
