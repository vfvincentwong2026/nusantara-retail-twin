"""`nrt serve` — 本地 HTTP 服务（docs/agent-bridge.md 的运行时入口）。

stdlib http.server，只读暴露种子与模拟产物：
- GET /health            → {"ok": true, "version": ...}
- GET /seeds             → 种子文件清单
- GET /seeds/<name>.json → 种子内容
- GET /simulations       → 模拟产物清单
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import typer
from rich.console import Console

console = Console()

ROOT = Path(__file__).resolve().parents[4]
SEEDS_DIR = ROOT / "data" / "seeds"
SIM_DIR = ROOT / "workspace" / "simulations"


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # 静音访问日志
        pass

    def _send(self, code: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.rstrip("/")
        if path == "/health":
            self._send(200, {"ok": True, "service": "nrt-serve"})
        elif path == "/seeds":
            self._send(200, [p.name for p in sorted(SEEDS_DIR.glob("*.json"))])
        elif path.startswith("/seeds/") and path.endswith(".json"):
            f = SEEDS_DIR / path[len("/seeds/"):]
            if f.is_file():
                self._send(200, json.loads(f.read_text(encoding="utf-8")))
            else:
                self._send(404, {"error": "not found"})
        elif path == "/simulations":
            self._send(200, [str(p.relative_to(SIM_DIR)) for p in sorted(SIM_DIR.rglob("*.json"))][:100])
        else:
            self._send(404, {"error": "not found", "routes": ["/health", "/seeds", "/seeds/<file>.json", "/simulations"]})


def serve(
    port: int = typer.Option(7101, "--port", "-p", help="监听端口"),
) -> None:
    """启动本地只读数据服务（Ctrl+C 停止）。"""
    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    console.print(f"[green]nrt serve 已启动[/green] http://127.0.0.1:{port} （Ctrl+C 停止）")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("已停止。")
    finally:
        server.server_close()
