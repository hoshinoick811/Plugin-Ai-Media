from __future__ import annotations

import pytest

pytest.importorskip("pallas.api.runtime")

import nonebot  # noqa: E402

nonebot.init(driver="nonebot.drivers.none:Driver")  # noqa: E402

from pallas_plugin_sing import ncm_login  # noqa: E402


@pytest.mark.asyncio
async def test_get_song_title_with_artist_returns_name_and_artists(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_track_detail(song_id):
        return {"songs": [{"name": "青花瓷", "id": song_id, "ar": [{"id": 1, "name": "周杰伦"}]}]}

    monkeypatch.setattr(ncm_login.ncm.track, "GetTrackDetail", fake_track_detail)
    result = await ncm_login.get_song_title_with_artist(123)
    assert result == ("青花瓷", ["周杰伦"])


@pytest.mark.asyncio
async def test_get_song_title_with_artist_falls_back_without_artists(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_track_detail(song_id):
        return {"songs": [{"name": "青花瓷", "id": song_id}]}

    monkeypatch.setattr(ncm_login.ncm.track, "GetTrackDetail", fake_track_detail)
    result = await ncm_login.get_song_title_with_artist(123)
    assert result == ("青花瓷", [])


@pytest.mark.asyncio
async def test_get_song_title_with_artist_returns_none_on_empty_name(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_track_detail(song_id):
        return {"songs": [{"id": song_id}]}

    monkeypatch.setattr(ncm_login.ncm.track, "GetTrackDetail", fake_track_detail)
    result = await ncm_login.get_song_title_with_artist(123)
    assert result is None


@pytest.mark.asyncio
async def test_get_song_title_with_artist_returns_none_on_empty_songs(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_track_detail(song_id):
        return {"songs": []}

    monkeypatch.setattr(ncm_login.ncm.track, "GetTrackDetail", fake_track_detail)
    result = await ncm_login.get_song_title_with_artist(123)
    assert result is None
