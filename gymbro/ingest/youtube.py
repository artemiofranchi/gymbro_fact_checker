"""YouTube ingestion: transcript (claims part) and video file (form part).

Run locally — YouTube often blocks cloud IPs.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..config import CACHE_DIR
from ..schema import TranscriptSegment, Video

_ID_RE = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})")


def video_id(url: str) -> str:
    m = _ID_RE.search(url)
    if not m:
        raise ValueError(f"Can't parse YouTube id from {url}")
    return m.group(1)


def fetch_transcript(vid: str, languages=("en",)) -> list[TranscriptSegment]:
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    fetched = api.fetch(vid, languages=list(languages))
    return [TranscriptSegment(t_start=s.start, t_end=s.start + s.duration, text=s.text)
            for s in fetched]


def download_video(url: str, out_dir: Path | None = None) -> str:
    import yt_dlp

    out_dir = out_dir or CACHE_DIR / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)
    opts = {"format": "mp4[height<=720]/best[height<=720]",
            "outtmpl": str(out_dir / "%(id)s.%(ext)s"), "quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


def load(url: str, with_video: bool = True) -> Video:
    vid = video_id(url)
    return Video(url=url, video_id=vid, transcript=fetch_transcript(vid),
                 local_path=download_video(url) if with_video else None)
