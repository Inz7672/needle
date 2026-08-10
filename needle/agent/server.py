import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_INDEX = Path(__file__).parent / "index.html"
_CACHE = {}


def _agent(tools_json):
    from .. import Needle
    if tools_json not in _CACHE:
        _CACHE.clear()
        _CACHE[tools_json] = Needle(tools=tools_json)
    return _CACHE[tools_json]


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            self._send(200, _INDEX.read_bytes(), "text/html")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/complete":
            self._send(404, b"not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            request = json.loads(self.rfile.read(length) or b"{}")
            tools = request.get("tools", [])
            tools_json = tools if isinstance(tools, str) else json.dumps(tools)
            result = _agent(tools_json).complete(request.get("query", ""))
            self._send(200, json.dumps(result))
        except Exception as exc:
            self._send(500, json.dumps({"error": str(exc)}))

    def log_message(self, *args):
        pass


def main(args):
    server = ThreadingHTTPServer((args.host, args.port), _Handler)
    print(f"needle playground: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
