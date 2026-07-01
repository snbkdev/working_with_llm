"""Парсинг YouTube-ссылок: из любого вида ссылки получаем id видео и таймкод.

Поддерживаются формы:
  https://www.youtube.com/watch?v=ID&t=1m30s
  https://youtu.be/ID?t=90
  https://www.youtube.com/embed/ID?start=90
  https://www.youtube.com/shorts/ID
  ID  (голый 11-символьный идентификатор)
"""
import re
from urllib.parse import parse_qs, urlparse

_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")
_TIME_RE = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")


def _parse_time(raw: str) -> int:
    """'90' / '90s' / '1m30s' / '1h2m3s' -> секунды."""
    raw = (raw or "").strip()
    if not raw:
        return 0
    if raw.isdigit():
        return int(raw)
    m = _TIME_RE.fullmatch(raw)
    if m and any(m.groups()):
        h, mi, s = (int(x) if x else 0 for x in m.groups())
        return h * 3600 + mi * 60 + s
    return 0


def parse_youtube(url: str) -> tuple[str | None, int]:
    """Вернуть (video_id, start_seconds). id = None, если ссылку не распознали."""
    url = (url or "").strip()
    if not url:
        return None, 0
    # Голый id.
    if _ID_RE.fullmatch(url):
        return url, 0

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    qs = parse_qs(parsed.query)
    parts = [p for p in parsed.path.split("/") if p]

    vid = None
    if "youtu.be" in host:
        vid = parts[0] if parts else None
    elif "youtube" in host:
        if parts and parts[0] in ("embed", "shorts", "v"):
            vid = parts[1] if len(parts) > 1 else None
        else:
            vid = (qs.get("v") or [None])[0]

    start = _parse_time((qs.get("t") or qs.get("start") or [""])[0])

    if vid and _ID_RE.fullmatch(vid):
        return vid, start
    return None, start
