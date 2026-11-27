#!/usr/bin/env python3
"""Efectos desde Openverse con acceso anónimo o credenciales OAuth opcionales.

Solo licencias que permiten uso comercial: CC0, dominio público (PDM) y CC BY. Fuera NC, ND, SA y Sampling+.
Cada sonido queda en <proyecto>/sonidos/openverse/<papel>/ con su ficha en manifiesto.json (título, autor,
licencia, enlace, atribución lista para pegar) y sus medidas (duración, brillo, ataque).

    python3 openverse.py buscar "soft whoosh" [--max-dur 2.5] [--n 10]
    python3 openverse.py bajar --papel transicion "soft whoosh" "swish air" [--n 3]
    python3 openverse.py recortar --papel tecleo "iphone typing"   # graba largas → toques sueltos
    python3 openverse.py lista [--papel transicion]
    python3 openverse.py creditos                                     # atribuciones CC BY para la descripción
Carpeta base: variable SONIDOS_DIR (por defecto ./sonidos).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np

BASE = Path(os.environ.get("SONIDOS_DIR", "sonidos")).resolve()
DEST = BASE / "openverse"
MANI = DEST / "manifiesto.json"
API = "https://api.openverse.org/v1/audio/"
TOKEN_URL = "https://api.openverse.org/v1/auth_tokens/token/"
_token = ""
_expira = 0.0
COMERCIAL = {"cc0", "pdm", "by"}
UA = {"User-Agent": "diseno-sonido-skill/1.0"}
FF = shutil.which("ffmpeg") or "ffmpeg"
SR = 48_000


class ErrorOpenverse(RuntimeError):
    """La API no pudo completar la operación."""


def _json_api(req: urllib.request.Request) -> dict:
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                if r.headers.get_content_type() != "application/json":
                    raise ErrorOpenverse(f"{req.selector.split('?')[0]} devolvió {r.headers.get_content_type()} en vez de JSON.")
                datos = json.load(r)
                if not isinstance(datos, dict):
                    raise ErrorOpenverse("Openverse devolvió un formato JSON inesperado.")
                return datos
        except urllib.error.HTTPError as e:
            ruta = req.selector.split("?")[0]
            if e.headers.get("cf-mitigated") == "challenge":
                ray = e.headers.get("cf-ray", "sin identificador")
                raise ErrorOpenverse(f"HTTP {e.code} en {ruta}. Cloudflare pide verificación. Ray ID {ray}.") from e
            if e.code not in (500, 502, 503, 504) or intento == 2:
                espera = e.headers.get("Retry-After")
                detalle = f" Retry-After: {espera}." if espera else ""
                raise ErrorOpenverse(f"HTTP {e.code} en {ruta}.{detalle}") from e
        except OSError as e:
            if intento == 2:
                raise ErrorOpenverse(f"No se pudo conectar con Openverse: {e}") from e
        except ValueError as e:
            raise ErrorOpenverse("Openverse envió una respuesta JSON ilegible.") from e
        time.sleep(3 * (intento + 1))


def _autorizacion() -> str:
    global _token, _expira
    cliente = os.environ.get("OPENVERSE_CLIENT_ID", "")
    secreto = os.environ.get("OPENVERSE_CLIENT_SECRET", "")
    if not cliente and not secreto:
        return ""
    if not cliente or not secreto:
        raise ErrorOpenverse("Configura juntas OPENVERSE_CLIENT_ID y OPENVERSE_CLIENT_SECRET.")
    if time.monotonic() >= _expira or not _token:
        datos = urllib.parse.urlencode(dict(grant_type="client_credentials", client_id=cliente,
                                            client_secret=secreto)).encode("ascii")
        req = urllib.request.Request(TOKEN_URL, data=datos, headers={**UA, "Accept": "application/json",
                                     "Content-Type": "application/x-www-form-urlencoded"})
        respuesta = _json_api(req)
        if not isinstance(respuesta.get("access_token"), str) or not respuesta["access_token"]:
            raise ErrorOpenverse("Openverse respondió sin token de acceso.")
        _token = respuesta["access_token"]
        _expira = time.monotonic() + max(0, int(respuesta.get("expires_in", 0)) - 30)
    return _token


def buscar(q: str, max_dur: float = 3.0, n: int = 10) -> list[dict]:
    params = {"q": q, "license": ",".join(sorted(COMERCIAL)), "page_size": 20}
    out = []
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={**UA, "Accept": "application/json"})
    token = _autorizacion()
    if token:
        req.add_unredirected_header("Authorization", f"Bearer {token}")
    respuesta = _json_api(req)
    if not isinstance(respuesta.get("results"), list):
        raise ErrorOpenverse("La respuesta de búsqueda de Openverse carece de una lista de resultados.")
    resultados = respuesta["results"]
    for r in resultados:
        lic = (r.get("license") or "").lower()
        dur = (r.get("duration") or 0) / 1000
        if lic not in COMERCIAL or not r.get("url") or not (0.05 < dur <= max_dur):
            continue
        out.append(dict(id=r["id"], titulo=r.get("title", ""), autor=r.get("creator", ""), licencia=lic,
                        version=r.get("license_version", ""), fuente=r.get("source", ""), dur=round(dur, 2),
                        url=r["url"], ficha=r.get("foreign_landing_url", "")))
        if len(out) >= n:
            break
    return out


def leer(ruta: Path, filtros: str = "") -> np.ndarray:
    af = ["-af", filtros] if filtros else []
    raw = subprocess.run([FF, "-v", "error", "-i", str(ruta), "-ac", "1", "-ar", str(SR), *af, "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def medir(ruta: Path) -> dict:
    x = leer(ruta)
    if not len(x):
        return {}
    n = min(len(x), 2 * SR)
    s = np.abs(np.fft.rfft(x[:n] * np.hanning(n)))
    f = np.fft.rfftfreq(n, 1 / SR)
    e = np.convolve(x ** 2, np.ones(480) / 480, "same")
    return dict(centroide_hz=round(float((s * f).sum() / max(1e-9, s.sum()))), ataque_s=round(float(np.argmax(e) / SR), 3),
                dur=round(len(x) / SR, 2))


def _cargar() -> dict:
    if not MANI.exists():
        return {"sonidos": []}
    try:
        return json.loads(MANI.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError:  # Manifiestos antiguos creados en Windows sin PYTHONUTF8.
        return json.loads(MANI.read_text(encoding="cp1252"))


def _guardar(m: dict) -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=MANI.parent) as temporal:
        archivo = Path(temporal) / "manifiesto.json"
        archivo.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
        archivo.replace(MANI)


def _licencia(r: dict) -> str:
    return {"cc0": "CC0", "pdm": "dominio público"}.get(r["licencia"], f"CC BY {r['version']}")


def _descargar(r: dict, destino: Path) -> tuple[Path, dict]:
    ext = Path(urllib.parse.urlparse(r["url"]).path).suffix or ".mp3"
    ruta = destino.with_suffix(ext)
    with tempfile.TemporaryDirectory(dir=destino.parent) as temporal:
        archivo = Path(temporal) / ruta.name
        with urllib.request.urlopen(urllib.request.Request(r["url"], headers=UA), timeout=60) as resp, archivo.open("wb") as f:
            shutil.copyfileobj(resp, f)
        medidas = medir(archivo)
        if not medidas:
            raise ValueError("El proveedor entregó un archivo sin audio medible.")
        archivo.replace(ruta)
    return ruta, medidas


def bajar(papel: str, consultas: list[str], n: int = 3, max_dur: float = 3.0) -> list[dict]:
    m = _cargar()
    ya = {s["id"] for s in m["sonidos"]}
    (DEST / papel).mkdir(parents=True, exist_ok=True)
    nuevos = []
    fallos = []
    for q in consultas:
        hechos = 0
        for r in buscar(q, max_dur, 20):
            if r["id"] in ya or hechos >= n:
                continue
            try:
                ruta, med = _descargar(r, DEST / papel / f"ov-{r['id'][:8]}")
            except Exception as e:  # noqa: BLE001
                fallos.append(str(e))
                print(f"  ✗ {r['titulo'][:40]}: {e}", file=sys.stderr)
                continue
            r.update(papel=papel, file=str(ruta.relative_to(BASE)), medidas=med,
                     atribucion=f"«{r['titulo']}» de {r['autor']} ({r['fuente']}), {_licencia(r)}: {r['ficha']}")
            m["sonidos"].append(r); nuevos.append(r); ya.add(r["id"]); hechos += 1
            _guardar(m)
            print(f"  ✓ {papel:11} {_licencia(r):10} {med.get('dur', 0):5.2f}s {med.get('centroide_hz', 0):5}Hz  {r['titulo'][:50]}")
    if fallos and not nuevos:
        raise ErrorOpenverse(f"Falló la descarga o la lectura del audio en el proveedor: {fallos[-1]}")
    return nuevos


def recortar(papel: str, consulta: str, max_toques: int = 14) -> int:
    """Baja la primera grabación larga que encaje (p. ej. alguien tecleando) y la parte en toques sueltos de 140 ms.
    Solo se quedan los toques con el golpe al principio (los que llevan dos toques pegados se descartan)."""
    m = _cargar()
    cand = [r for r in buscar(consulta, 30, 10) if r["dur"] > 2]
    if not cand:
        print("sin grabaciones largas para esa búsqueda"); return 0
    r = cand[0]
    (DEST / papel).mkdir(parents=True, exist_ok=True)
    src, _ = _descargar(r, DEST / f"_fuente-{r['id'][:8]}")
    x = leer(src, "highpass=f=120")
    v = 240
    e = 10 * np.log10(np.add.reduceat(x[: len(x) // v * v] ** 2, np.arange(0, len(x) // v * v, v)) / v + 1e-12)
    umbral, k, ult = np.percentile(e, 95) - 6, 0, -999
    for i in range(1, len(e) - 1):
        if not (e[i] > umbral and e[i] >= e[i - 1] and e[i] >= e[i + 1] and i - ult > 20):
            continue
        ult = i
        a = max(0, i * v - 480)
        seg = x[a:a + int(0.14 * SR)].copy()
        if len(seg) < 2400 or np.abs(seg).max() < 0.02:
            continue
        seg[-960:] *= np.linspace(1, 0, 960)
        ruta = DEST / papel / f"{papel}-{r['id'][:6]}-{k:02d}.wav"
        with wave.open(str(ruta), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(seg / np.abs(seg).max() * 0.8, -1, 1) * 32767).astype("<i2").tobytes())
        med = medir(ruta)
        if med.get("ataque_s", 1) >= 0.03:
            ruta.unlink(); continue
        m["sonidos"].append(dict(id=f"{r['id']}-t{k:02d}", titulo=f"{r['titulo']} (toque {k})", autor=r["autor"],
                                 licencia=r["licencia"], version=r["version"], fuente=r["fuente"], papel=papel,
                                 file=str(ruta.relative_to(BASE)), ficha=r["ficha"], medidas=med,
                                 atribucion=f"«{r['titulo']}» de {r['autor']} ({r['fuente']}), {_licencia(r)}: {r['ficha']}"))
        k += 1
        if k >= max_toques:
            break
    _guardar(m)
    print(f"  ✓ {k} toques de «{r['titulo']}» ({_licencia(r)})")
    return k


def lista(papel: str | None = None) -> list[dict]:
    return [s for s in _cargar()["sonidos"] if papel in (None, s["papel"]) and not s.get("fuera")]


def creditos(ids=None) -> str:
    return "\n".join(s["atribucion"] for s in _cargar()["sonidos"]
                     if s["licencia"] == "by" and (ids is None or s["id"] in ids))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("buscar"); b.add_argument("q"); b.add_argument("--max-dur", type=float, default=3.0); b.add_argument("--n", type=int, default=10)
    d = sub.add_parser("bajar"); d.add_argument("--papel", required=True); d.add_argument("q", nargs="+"); d.add_argument("--n", type=int, default=3); d.add_argument("--max-dur", type=float, default=3.0)
    c = sub.add_parser("recortar"); c.add_argument("--papel", required=True); c.add_argument("q")
    li = sub.add_parser("lista"); li.add_argument("--papel")
    sub.add_parser("creditos")
    a = ap.parse_args()
    if a.cmd == "buscar":
        for r in buscar(a.q, a.max_dur, a.n):
            print(f"{r['licencia']:4} {r['dur']:5.2f}s {r['fuente']:10} {r['titulo'][:60]}")
    elif a.cmd == "bajar":
        bajar(a.papel, a.q, a.n, a.max_dur)
    elif a.cmd == "recortar":
        recortar(a.papel, a.q)
    elif a.cmd == "lista":
        for s in lista(a.papel):
            print(f"{s['papel']:11} {s['licencia']:4} {s['medidas'].get('dur', 0):5.2f}s {s['medidas'].get('centroide_hz', 0):5}Hz {s['titulo'][:50]}")
    else:
        print(creditos() or "(sin sonidos CC BY)")


if __name__ == "__main__":
    try:
        main()
    except ErrorOpenverse as error:
        sys.exit(f"Openverse: {error}")
