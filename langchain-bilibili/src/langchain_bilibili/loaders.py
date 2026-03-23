from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .transcribe import download_bilibili_audio, transcribe_with_whisper

DEFAULT_SAMPLE = Path(__file__).resolve().parents[2] / "sample_data" / "sample_video.txt"
DEFAULT_VIDEO_INDEX = Path(__file__).resolve().parents[2] / "sample_data" / "bilibili_videos.json"


@dataclass(frozen=True)
class VideoSource:
    source_type: str
    title: str
    identifier: str
    uploader: str
    description: str
    transcript_path: Path
    url: str | None = None


def read_transcript(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def extract_bvid(value: str) -> str:
    text = value.strip()
    pattern = re.compile(r"(BV[0-9A-Za-z]+)")
    matched = pattern.search(text)
    if matched:
        return matched.group(1)
    raise ValueError(f"Unable to parse BV id from input: {value}")


def load_video_index(index_path: Path = DEFAULT_VIDEO_INDEX) -> dict[str, dict[str, str]]:
    return json.loads(index_path.read_text(encoding="utf-8"))


def load_local_source(path: Path) -> VideoSource:
    return VideoSource(
        source_type="local",
        title=path.stem,
        identifier=str(path),
        uploader="local",
        description="Local transcript file",
        transcript_path=path,
    )


def load_bilibili_source(value: str, index_path: Path = DEFAULT_VIDEO_INDEX) -> VideoSource:
    bvid = extract_bvid(value)
    index = load_video_index(index_path)
    if bvid not in index:
        raise KeyError(
            f"BV id {bvid} is not available in the local sample index: {index_path}"
        )

    record = index[bvid]
    transcript_path = Path(record["transcript_path"])
    if not transcript_path.is_absolute():
        transcript_path = index_path.parents[1] / transcript_path

    return VideoSource(
        source_type="bilibili",
        title=record["title"],
        identifier=bvid,
        uploader=record["uploader"],
        description=record["description"],
        transcript_path=transcript_path,
        url=f"https://www.bilibili.com/video/{bvid}",
    )


def resolve_real_bilibili_source(value: str) -> VideoSource:
    bvid = extract_bvid(value)
    url = value if value.startswith("http") else f"https://www.bilibili.com/video/{bvid}"
    audio_path = download_bilibili_audio(url, bvid)
    transcript_path = transcribe_with_whisper(audio_path, bvid)
    return VideoSource(
        source_type="bilibili",
        title=bvid,
        identifier=bvid,
        uploader="unknown",
        description="Downloaded from Bilibili and transcribed locally",
        transcript_path=transcript_path,
        url=url,
    )


def resolve_source(
    input_path: Path | None = None,
    bv: str | None = None,
    url: str | None = None,
    use_real_bilibili: bool = False,
) -> VideoSource:
    if input_path:
        return load_local_source(input_path)
    if bv:
        if use_real_bilibili:
            return resolve_real_bilibili_source(bv)
        return load_bilibili_source(bv)
    if url:
        if use_real_bilibili:
            return resolve_real_bilibili_source(url)
        return load_bilibili_source(url)
    return load_local_source(DEFAULT_SAMPLE)
