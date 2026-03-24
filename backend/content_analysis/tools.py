from __future__ import annotations

import os
import shutil


def binary_override_env(name: str) -> str:
    normalized = name.replace("-", "_").upper()
    return f"{normalized}_BIN"


def find_binary(name: str) -> str | None:
    override = os.getenv(binary_override_env(name), "").strip()
    if override:
        return override
    return shutil.which(name)


def require_binary(name: str) -> str:
    binary = find_binary(name)
    if binary is None:
        override_env = binary_override_env(name)
        install_hint = {
            "yt-dlp": "pipx install yt-dlp",
            "whisper": "pipx install openai-whisper",
        }.get(name, f"Please install '{name}' and ensure it is available in PATH.")
        raise RuntimeError(
            f"Required executable '{name}' was not found in PATH. "
            f"You can also set {override_env} to the executable path. "
            f"Install hint: {install_hint}"
        )
    return binary
