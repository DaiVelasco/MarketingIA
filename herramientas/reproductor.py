"""Crea una vista del reel que se puede abrir directamente en un navegador."""
import argparse
import base64
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from entrega_archivos import publicar_archivo


def preparar(master, destino, ffmpeg):
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destino.parent) as tmp:
        video = Path(tmp) / "reel.webm"
        subprocess.run([ffmpeg, "-hide_banner", "-v", "error", "-nostdin", "-xerror", "-i", str(master),
                        "-map", "0:v:0", "-map", "0:a:0", "-vf", "scale=540:-2,setsar=1",
                        "-c:v", "libvpx-vp9", "-crf", "33", "-b:v", "0", "-row-mt", "1", "-cpu-used", "5",
                        "-threads", "4", "-pix_fmt", "yuv420p", "-c:a", "libopus", "-b:a", "96k",
                        str(video)], check=True)
        encoded = base64.b64encode(video.read_bytes()).decode("ascii")
        title = html.escape(master.stem)
        page = Path(tmp) / "reel.html"
        page.write_text(f"""<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>html,body{{margin:0;background:#121413;color:white;height:100%}}body{{display:grid;place-items:center}}
video{{max-height:100vh;max-height:100dvh;max-width:100%;width:auto;display:block}}</style>
<video controls playsinline preload="auto" aria-label="{title}" src="data:video/webm;base64,{encoded}"></video>
</html>""", encoding="utf-8")
        publicar_archivo(video, destino.with_suffix(".webm"))
        publicar_archivo(page, destino)


def servir(page):
    class Player(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?", 1)[0] != "/":
                self.send_error(404)
                return
            body = page.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    if not page.is_file():
        raise SystemExit("Falta la página del reproductor.")
    with ThreadingHTTPServer(("127.0.0.1", 0), Player) as server:
        print(f"http://127.0.0.1:{server.server_port}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(required=True, dest="cmd")
    create = sub.add_parser("preparar")
    create.add_argument("master", type=Path)
    create.add_argument("html", type=Path)
    local = Path(__file__).resolve().parents[1] / ".local/ffmpeg.exe"
    create.add_argument("--ffmpeg", default=os.environ.get("MARKETINGIA_FFMPEG") or
                        (str(local) if local.is_file() else shutil.which("ffmpeg")))
    serve = sub.add_parser("servir")
    serve.add_argument("html", type=Path)
    args = parser.parse_args()
    if args.cmd == "servir":
        servir(args.html)
    elif args.ffmpeg and args.html.suffix.lower() == ".html":
        preparar(args.master, args.html, args.ffmpeg)
    else:
        parser.error("Indica un destino .html y una instalación de FFmpeg.")
