from __future__ import annotations

import shutil


def find_binary(name: str) -> str | None:
    return shutil.which(name)


def require_binary(name: str) -> str:
    binary = find_binary(name)
    if binary is None:
        install_hint = {
            "yt-dlp": "pipx install yt-dlp",
            "whisper": "pipx install openai-whisper",
        }.get(name, f"Please install '{name}' and ensure it is available in PATH.")
        raise RuntimeError(
            f"Required executable '{name}' was not found in PATH. "
            f"Install hint: {install_hint}"
        )
    return binary
