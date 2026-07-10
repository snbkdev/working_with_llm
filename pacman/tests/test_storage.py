"""Сохранение настроек: дефолты, round-trip, устойчивость к битому файлу."""

from src import storage


def test_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_PATH", tmp_path / "save.json")
    data = storage.load()
    assert data == {"high": 0, "sound": True, "volume": 0.7}


def test_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_PATH", tmp_path / "save.json")
    storage.save({"high": 4200, "sound": False, "volume": 0.3, "junk": 1})
    data = storage.load()
    assert data["high"] == 4200
    assert data["sound"] is False
    assert data["volume"] == 0.3
    assert "junk" not in data        # пишем только известные ключи


def test_broken_file_falls_back(tmp_path, monkeypatch):
    p = tmp_path / "save.json"
    p.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(storage, "_PATH", p)
    assert storage.load() == {"high": 0, "sound": True, "volume": 0.7}
