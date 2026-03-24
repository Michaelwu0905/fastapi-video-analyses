from __future__ import annotations

import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://100.74.44.119:8000").rstrip("/")
HOST = os.getenv("VOLCANO_PROXY_HOST", "0.0.0.0")
PORT = int(os.getenv("VOLCANO_PROXY_PORT", "8000"))


class ProxyHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        path = path.split("?", 1)[0].split("#", 1)[0]
        relative = path.lstrip("/") or "index.html"
        return str((FRONTEND_DIST_DIR / relative).resolve())

    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            self._proxy_request()
            return

        candidate = FRONTEND_DIST_DIR / self.path.lstrip("/")
        if self.path in {"/", ""} or not candidate.exists() or candidate.is_dir():
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self) -> None:
        self._proxy_request()

    def do_PUT(self) -> None:
        self._proxy_request()

    def do_DELETE(self) -> None:
        self._proxy_request()

    def do_OPTIONS(self) -> None:
        self._proxy_request()

    def _proxy_request(self) -> None:
        target_url = urljoin(f"{BACKEND_BASE_URL}/", self.path.lstrip("/"))
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "content-length", "connection"}
        }
        headers["Host"] = BACKEND_BASE_URL.removeprefix("http://").removeprefix("https://")

        request = Request(target_url, data=body, headers=headers, method=self.command)
        try:
            with urlopen(request, timeout=300) as response:
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() in {"transfer-encoding", "connection"}:
                        continue
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
        except HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                if key.lower() in {"transfer-encoding", "connection"}:
                    continue
                self.send_header(key, value)
            self.end_headers()
            if payload:
                self.wfile.write(payload)
        except URLError as exc:
            payload = f'{{"detail":"代理后端不可达: {exc.reason}"}}'.encode("utf-8")
            self.send_response(HTTPStatus.BAD_GATEWAY)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)


def main() -> None:
    if not (FRONTEND_DIST_DIR / "index.html").exists():
        raise SystemExit(f"未找到前端构建产物: {FRONTEND_DIST_DIR}")

    server = ThreadingHTTPServer((HOST, PORT), ProxyHandler)
    print(f"volcano proxy serving {FRONTEND_DIST_DIR} at http://{HOST}:{PORT}")
    print(f"proxying /api -> {BACKEND_BASE_URL}")
    server.serve_forever()


if __name__ == "__main__":
    main()
