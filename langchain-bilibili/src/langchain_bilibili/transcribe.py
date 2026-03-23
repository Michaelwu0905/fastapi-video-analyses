from __future__ import annotations

import subprocess
from pathlib import Path

from .config import (
    DOWNLOADS_DIR,
    TRANSCRIPTS_DIR,
    ensure_artifact_dirs,
    load_whisper_settings,
)
from .tools import require_binary


def download_bilibili_audio(url: str, bvid: str) -> Path:
    ensure_artifact_dirs()
    yt_dlp = require_binary("yt-dlp")
    existing = sorted(DOWNLOADS_DIR.glob(f"{bvid}.*"))
    if existing:
        return existing[0]
    output_template = DOWNLOADS_DIR / f"{bvid}.%(ext)s"
    command = [
        yt_dlp,
        "-f",
        "bestaudio/best",
        "-o",
        str(output_template),
        url,
    ]
    subprocess.run(command, check=True)

    candidates = sorted(DOWNLOADS_DIR.glob(f"{bvid}.*"))
    if not candidates:
        raise RuntimeError(f"Audio download completed but no file was created for {bvid}.")
    return candidates[0]


def transcribe_with_whisper(audio_path: Path, bvid: str) -> Path:
    ensure_artifact_dirs()
    whisper = require_binary("whisper")
    transcript_path = TRANSCRIPTS_DIR / f"{bvid}.txt"
    if transcript_path.exists():
        return transcript_path
    settings = load_whisper_settings()
    command = [
        whisper,
        str(audio_path),
        "--model",
        settings.model,
        "--task",
        "transcribe",
        "--language",
        settings.language,
        "--output_format",
        "txt",
        "--output_dir",
        str(TRANSCRIPTS_DIR),
    ]
    subprocess.run(command, check=True)
    if not transcript_path.exists():
        txt_candidates = sorted(TRANSCRIPTS_DIR.glob(f"{audio_path.stem}*.txt"))
        if txt_candidates:
            txt_candidates[0].replace(transcript_path)
    if not transcript_path.exists():
        raise RuntimeError(f"Whisper transcription did not create {transcript_path}.")
    return transcript_path
