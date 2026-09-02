from datetime import datetime, timedelta, timezone

from nyc_movie_alert import state


def test_mark_and_check_notified():
    s = {}
    assert not state.already_notified(s, "Blade Runner", "Film Forum")
    state.mark_notified(s, "Blade Runner", "Film Forum")
    assert state.already_notified(s, "Blade Runner", "Film Forum")


def test_different_theater_is_independent():
    s = {}
    state.mark_notified(s, "Blade Runner", "Film Forum")
    assert not state.already_notified(s, "Blade Runner", "IFC Center")


def test_cooldown_expired():
    s = {}
    key = state._key("Blade Runner", "Film Forum")
    old = datetime.now(timezone.utc) - timedelta(days=state.COOLDOWN_DAYS + 1)
    s[key] = old.isoformat()
    assert not state.already_notified(s, "Blade Runner", "Film Forum")


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    s = {}
    state.mark_notified(s, "Blade Runner", "Film Forum")
    state.save(s, path=path)
    loaded = state.load(path=path)
    assert state.already_notified(loaded, "Blade Runner", "Film Forum")
