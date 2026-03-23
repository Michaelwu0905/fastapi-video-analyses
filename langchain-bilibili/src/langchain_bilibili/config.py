from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"
DOWNLOADS_DIR = ARTIFACTS_DIR / "downloads"
TRANSCRIPTS_DIR = ARTIFACTS_DIR / "transcripts"


@dataclass(frozen=True)
class MoonshotSettings:
    api_key: str
    base_url: str
    model: str


@dataclass(frozen=True)
class WhisperSettings:
    model: str
    language: str


def ensure_artifact_dirs() -> None:
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> MoonshotSettings:
    load_dotenv(ENV_FILE)
    return MoonshotSettings(
        api_key=os.getenv("MOONSHOT_API_KEY", "").strip(),
        base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1").strip(),
        model=os.getenv("MOONSHOT_MODEL", "kimi-k2-0711-preview").strip(),
    )


def load_whisper_settings() -> WhisperSettings:
    load_dotenv(ENV_FILE)
    return WhisperSettings(
        model=os.getenv("WHISPER_MODEL", "base").strip(),
        language=os.getenv("WHISPER_LANGUAGE", "zh").strip(),
    )
