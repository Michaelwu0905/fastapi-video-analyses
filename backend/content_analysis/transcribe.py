from __future__ import annotations

import subprocess
from pathlib import Path

from .config import (
    DOWNLOADS_DIR,
    TRANSCRIPTS_DIR,
    ensure_artifact_dirs,
    load_transcription_settings,
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


def _write_transcript(path: Path, text: str) -> Path:
    normalized = "\n".join(line for line in text.splitlines() if line.strip()).strip()
    if not normalized:
        raise RuntimeError(f"Transcription completed but produced empty output for {path.stem}.")
    path.write_text(normalized + "\n", encoding="utf-8")
    return path


def transcribe_with_whisper_cli(audio_path: Path, bvid: str) -> Path:
    ensure_artifact_dirs()
    whisper = require_binary("whisper")
    transcript_path = TRANSCRIPTS_DIR / f"{bvid}.txt"
    if transcript_path.exists():
        return transcript_path
    settings = load_transcription_settings()
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


def transcribe_with_faster_whisper(audio_path: Path, bvid: str) -> Path:
    ensure_artifact_dirs()
    transcript_path = TRANSCRIPTS_DIR / f"{bvid}.txt"
    if transcript_path.exists():
        return transcript_path

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Install hint: uv add faster-whisper"
        ) from exc

    settings = load_transcription_settings()
    model_source = settings.faster_whisper_model_path or settings.model
    model = WhisperModel(
        model_source,
        device=settings.faster_whisper_device,
        compute_type=settings.faster_whisper_compute_type,
        download_root=settings.faster_whisper_download_root or None,
        local_files_only=settings.faster_whisper_local_files_only,
    )
    segments, _ = model.transcribe(
        str(audio_path),
        language=settings.language,
        task="transcribe",
        vad_filter=True,
    )
    transcript_text = "\n".join(segment.text.strip() for segment in segments if segment.text.strip())
    if not transcript_text.strip():
        print(f"[转写] {bvid} 在开启 VAD 时未产出文本，自动重试无 VAD 模式")
        retry_segments, _ = model.transcribe(
            str(audio_path),
            language=settings.language,
            task="transcribe",
            vad_filter=False,
        )
        transcript_text = "\n".join(
            segment.text.strip() for segment in retry_segments if segment.text.strip()
        )
    return _write_transcript(transcript_path, transcript_text)


def transcribe_audio(audio_path: Path, bvid: str) -> Path:
    settings = load_transcription_settings()
    backend = settings.backend.lower()

    if backend == "whisper_cli":
        return transcribe_with_whisper_cli(audio_path, bvid)

    if backend == "faster_whisper":
        return transcribe_with_faster_whisper(audio_path, bvid)

    if backend == "auto":
        try:
            return transcribe_with_faster_whisper(audio_path, bvid)
        except Exception as exc:
            print(f"[转写] faster-whisper 不可用，回退到 whisper CLI：{exc}")
            return transcribe_with_whisper_cli(audio_path, bvid)

    raise RuntimeError(
        f"Unsupported TRANSCRIBE_BACKEND={settings.backend!r}. "
        "Expected one of: auto, faster_whisper, whisper_cli."
    )
