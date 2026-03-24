from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
PROJECT_ENV_FILE = BACKEND_DIR / ".env"
ROOT_ENV_FILE = BACKEND_DIR.parent / ".env"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DOWNLOADS_DIR = ARTIFACTS_DIR / "downloads"
TRANSCRIPTS_DIR = ARTIFACTS_DIR / "transcripts"


@dataclass(frozen=True)
class MoonshotSettings:
    api_key: str
    base_url: str
    model: str


@dataclass(frozen=True)
class TranscriptionSettings:
    backend: str
    model: str
    language: str
    faster_whisper_device: str
    faster_whisper_compute_type: str
    faster_whisper_model_path: str
    faster_whisper_download_root: str
    faster_whisper_local_files_only: bool


def ensure_artifact_dirs() -> None:
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


def load_project_env() -> None:
    load_dotenv(ROOT_ENV_FILE)
    load_dotenv(PROJECT_ENV_FILE)


def load_settings() -> MoonshotSettings:
    load_project_env()
    return MoonshotSettings(
        api_key=os.getenv("MOONSHOT_API_KEY", "").strip(),
        base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1").strip(),
        model=os.getenv("MOONSHOT_MODEL", "kimi-k2-0711-preview").strip(),
    )


def load_transcription_settings() -> TranscriptionSettings:
    load_project_env()
    return TranscriptionSettings(
        backend=os.getenv("TRANSCRIBE_BACKEND", "auto").strip(),
        model=os.getenv("WHISPER_MODEL", "base").strip(),
        language=os.getenv("WHISPER_LANGUAGE", "zh").strip(),
        faster_whisper_device=os.getenv("FASTER_WHISPER_DEVICE", "cuda").strip(),
        faster_whisper_compute_type=os.getenv("FASTER_WHISPER_COMPUTE_TYPE", "float16").strip(),
        faster_whisper_model_path=os.getenv("FASTER_WHISPER_MODEL_PATH", "").strip(),
        faster_whisper_download_root=os.getenv("FASTER_WHISPER_DOWNLOAD_ROOT", "").strip(),
        faster_whisper_local_files_only=os.getenv("FASTER_WHISPER_LOCAL_FILES_ONLY", "").strip().lower() in {"1", "true", "yes", "on"},
    )
