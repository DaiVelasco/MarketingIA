#!/usr/bin/env python3
"""Motor de diseño de sonido: coloca, nivela y mezcla efectos sobre un vídeo como lo haría un diseñador de sonido.

Fuentes de sonido (por papel): tu carpeta <SONIDOS_DIR>/<papel>/ (los que tú elijas) + lo bajado de Openverse
(openverse.py, solo CC0 / CC BY). Reglas medidas (ver SKILL.md): varias tomas en rotación, colocación por llegada o
pico, mapa de voz para no tapar a quien habla, estéreo por posición, secuencias que suben de tono, sonoridad por papel
y máster a −14 LUFS (con voz) o −16 (efectos solos), con informe de calidad.

Uso (Python):
    import diseno
    eventos = [(0.15, "pop", {"x": 540}), (0.55, "transicion", {}), (2.75, "secuencia", {"paso": 0}), ...]
    diseno.mezclar(eventos, dur=8.5, salida="sfx.wav", voz="voz.wav")       # voz opcional
CLI:
    python3 diseno.py tomas <papel>
    python3 diseno.py mezclar eventos.json --dur 8.5 --salida sfx.wav [--voz voz.wav] [--ganancia 3]
    (eventos.json = [[t, "papel", {opciones}], ...])
"""
from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import openverse as OV  # noqa: E402

FF = shutil.which("ffmpeg") or "ffmpeg"
SR = 48_000
AUDIO = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aif", ".aiff"}

# papel → (carpetas, colocación, desfase s, brillo máximo Hz, sonoridad objetivo dBFS en 0,4 s)
PAPELES = {
    "texto":      (["texto"], "llegada", -0.02, 3200, -19),
    "icono":      (["icono", "pop"], "llegada", +0.01, 3200, -18),
    "pop":        (["pop", "icono"], "llegada", +0.03, 3200, -18),
    "transicion": (["transicion"], "pico", 0.0, 3200, -20),
    "pantalla":   (["pantalla", "transicion"], "llegada", -0.01, 6500, -19),
    "clic":       (["clic"], "llegada", -0.011, 4000, -19),
    "exito":      (["exito"], "llegada", 0.0, 4500, -19),
    "secuencia":  (["secuencia", "clic"], "llegada", -0.01, 3200, -20),
    "tecleo":     (["tecleo"], "llegada", -0.005, 5600, -21),
    "tension":    (["tension"], "fin", 0.0, 3200, -21),
    "revelacion": (["revelacion"], "llegada", 0.0, 3200, -17),
    "cifra":      (["cifra"], "llegada", 0.0, 3200, -21),
}
GRANDES = {"exito", "revelacion", "tension"}


def _leer(ruta: Path) -> np.ndarray:
    return OV.leer(ruta, "highpass=f=90,lowpass=f=8000,afade=t=in:d=0.002,areverse,afade=t=in:d=0.015,areverse")


def _centroide(x):
    n = min(len(x), SR)
    s = np.abs(np.fft.rfft(x[:n] * np.hanning(n)))
    f = np.fft.rfftfreq(n, 1 / SR)
    return float((s * f).sum() / max(1e-9, s.sum()))


def cuerpo(x, sala: float = 0.45, drive: float = 3.0):
    """Un clic de menos de 0,5 s no se oye bajo la voz aunque su pico esté alto: cola de sala corta + saturación suave."""
    t = np.arange(int(0.16 * SR)) / SR
    ir = np.random.default_rng(1).normal(0, 1, len(t)) * np.exp(-t / 0.035)
    ir /= np.sqrt((ir ** 2).sum())
    wet = np.convolve(x, ir)
    y = np.zeros(len(wet)); y[:len(x)] += x; y += sala * wet
    y = y / max(float(np.abs(y).max()), 1e-9)
    return (np.tanh(drive * y) / np.tanh(drive)).astype(np.float32)


def nivelar(x, objetivo_db: float, techo_db: float = -2.0):
    """Sonoridad por papel: máximo de energía en ventanas de 0,4 s = objetivo (como el oído), pico ≤ techo."""
    x = np.asarray(x, np.float32)
    if len(x) < 0.5 * SR:
        x = cuerpo(x)
    v = int(0.4 * SR)
    c = np.concatenate([[0.0], np.cumsum(x.astype(np.float64) ** 2)])
    m = ((c[v:] - c[:-v]) / v).max() if len(x) > v else float(np.mean(x ** 2)) * len(x) / v
    g = 10 ** (objetivo_db / 20) / max(float(np.sqrt(m)), 1e-9)
    pico = float(np.abs(x).max()) * g
    if pico > 10 ** (techo_db / 20):
        g *= 10 ** (techo_db / 20) / pico
    return x * g


def tomas(papel: str, variante: str | None = None) -> list[dict]:
    """Las tomas válidas de un papel: tu carpeta y Openverse, sin las demasiado brillantes. Lo tuyo va primero."""
    carpetas, _c, _o, techo, _n = PAPELES[papel]
    out = []
    for c in carpetas:
        d = OV.BASE / c
        if d.is_dir():
            out += [dict(id=p.stem, ruta=p, fuente="propia") for p in sorted(d.iterdir()) if p.suffix.lower() in AUDIO]
        for s in OV.lista(c):
            if variante and variante not in s["file"]:
                continue
            out.append(dict(id="ov-" + Path(s["file"]).stem, ruta=OV.BASE / s["file"], fuente="openverse",
                            atribucion=s["atribucion"], licencia=s["licencia"]))
    vale = []
    for t in out:
        x = _leer(t["ruta"])
        if len(x) and (t["fuente"] == "propia" or _centroide(x) <= techo):
            t["x"] = x
            vale.append(t)
    return vale[:8]


def _punto(x, tipo: str) -> float:
    v = SR // 100
    e = np.add.reduceat(x[: len(x) // v * v] ** 2, np.arange(0, len(x) // v * v, v))
    if not len(e):
        return 0.0
    if tipo == "pico":
        return float(np.argmax(e) * v / SR)
    if tipo == "fin":
        return float((len(e) - 1 - np.argmax(e[::-1] >= e.max() * 10 ** (-12 / 10))) * v / SR)
    return float(np.argmax(e >= e.max() * 10 ** (-6 / 10)) * v / SR)


def mapa_voz(voz: np.ndarray) -> np.ndarray:
    raw = subprocess.run([FF, "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                          "highpass=f=250,lowpass=f=3800", "-f", "f32le", "-"], input=voz.astype(np.float32).tobytes(),
                         capture_output=True, check=True).stdout
    b = np.frombuffer(raw, np.float32)
    v = SR // 100
    if len(b) < v:
        return np.zeros(1, bool)
    e = 10 * np.log10(np.add.reduceat(b[: len(b) // v * v] ** 2, np.arange(0, len(b) // v * v, v)) / v + 1e-12)
    m = e > np.percentile(e, 10) + 12
    hueco = 0
    for i in range(len(m)):
        if m[i]:
            if 0 < hueco < 15:
                m[i - hueco:i] = True
            hueco = 0
        else:
            hueco += 1
    return m


def _pitch(x, st):
    if abs(st) < 0.01:
        return x
    idx = np.arange(0, len(x) - 1, 2 ** (st / 12))
    return np.interp(idx, np.arange(len(x)), x).astype(np.float32)


def _paso_alto(x):
    y = subprocess.run([FF, "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", "highpass=f=400",
                        "-f", "f32le", "-"], input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(y, np.float32)


def disenar(eventos, dur: float, voz: np.ndarray | None = None, ganancia_db: float = 0.0, variantes=None, semilla: int = 7):
    rng = random.Random(semilla)
    n = math.ceil((dur + 0.3) * SR)
    cama = np.zeros((n, 2), np.float32)
    voz_m = mapa_voz(voz) if voz is not None and len(voz) else np.zeros(1, bool)
    pools, ultimo, hechos = {}, {}, []
    for t, papel, o in sorted(eventos, key=lambda e: e[0]):
        if papel not in pools:
            pools[papel] = tomas(papel, (variantes or {}).get(papel))
        pool = pools[papel]
        if not pool:
            print(f"  ⚠ sin tomas para «{papel}»: baja algunas con openverse.py bajar --papel {papel} …", file=sys.stderr)
            continue
        cand = [p for p in pool if p["id"] != ultimo.get(papel)] or pool
        if o.get("toma") and any(p["id"] == o["toma"] for p in pool):
            tom = next(p for p in pool if p["id"] == o["toma"])
        elif papel == "clic":
            tom = pool[0]                                         # un clic de UI: una sola voz
        elif o.get("paso", 0) > 0 and papel in ultimo:
            tom = next(p for p in pool if p["id"] == ultimo[papel])   # secuencia: misma toma subiendo de tono
        else:
            tom = rng.choice(cand)
        ultimo[papel] = tom["id"]
        _c, col, off, _t, nivel = PAPELES[papel]
        x = nivelar(tom["x"], nivel + ganancia_db)
        st = (rng.uniform(-0.4, 0.4) if "paso" not in o else 0.0) + 0.55 * o.get("paso", 0)
        x = _pitch(x, st) * 10 ** (rng.uniform(-1.5, 1.5) / 20)
        i0 = max(0, round((t + off - _punto(x, col)) * SR))
        k = min(len(voz_m) - 1, max(0, int(t * 100)))
        sobre_voz = bool(voz_m[k:k + 6].mean() > 0.8) if len(voz_m) > 1 else False
        if sobre_voz:
            x = _paso_alto(x) * (0.35 if papel in GRANDES else 0.71)
        pan = max(-0.35, min(0.35, (o.get("x", 540) - 540) / 540 * 0.35))
        a = (pan + 1) * math.pi / 4
        largo = min(len(x), n - i0)
        if largo > 0:
            cama[i0:i0 + largo, 0] += x[:largo] * math.cos(a)
            cama[i0:i0 + largo, 1] += x[:largo] * math.sin(a)
        hechos.append(dict(t=round(t, 3), papel=papel, toma=tom["id"], fuente=tom["fuente"], sobre_voz=sobre_voz,
                           secuencia="paso" in o, st=round(st, 2), pan=round(pan, 2), atribucion=tom.get("atribucion")))
    return cama, hechos


def _lufs(ruta: Path) -> tuple[float, float]:
    o = subprocess.run([FF, "-hide_banner", "-nostats", "-i", str(ruta), "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    i0 = o.rindex("{")
    j = json.loads(o[i0:o.index("}", i0) + 1])
    return float(j["input_i"]), float(j["input_tp"])


def informe(hechos, dur: float, master: Path | None = None, max_10s: float = 8.0) -> dict:
    ts = [h["t"] for h in hechos]
    rafaga = {"pop", "tecleo", "secuencia"}
    gestos = [h for i, h in enumerate(hechos) if not (h["papel"] in rafaga and i and hechos[i - 1]["papel"] == h["papel"])]
    huecos = [round(b - a, 2) for a, b in zip([0.0] + ts, ts + [dur]) if b - a > 4.0]
    seguidas, rep = 1, 0
    for a, b in zip(hechos, hechos[1:]):
        seguidas = seguidas + 1 if a["toma"] == b["toma"] and not b["secuencia"] and b["papel"] != "tecleo" else 1
        rep += seguidas == 5
    r = dict(efectos=len(hechos), por_10s=round(len(gestos) / max(dur, 1) * 10, 1), en_2_primeros_s=any(t <= 2 for t in ts),
             huecos_4s=huecos, rafagas_repetidas=rep, sobre_voz=sum(h["sobre_voz"] for h in hechos),
             tomas_distintas=len({h["toma"] for h in hechos}))
    if master:
        r["lufs"], r["pico_real"] = _lufs(master)
    r["avisos"] = [m for c, m in ((r["por_10s"] > max_10s, f"más de {max_10s:g} gestos cada 10 s"),
                                  (not r["en_2_primeros_s"], "nada suena en los 2 primeros segundos"),
                                  (bool(huecos), f"huecos sin sonido de más de 4 s: {huecos}"),
                                  (rep > 0, "5 tomas iguales seguidas"),
                                  (r.get("pico_real", -9) > -1.0, "pico real por encima de −1 dBTP")) if c]
    return r


def mezclar(eventos, dur: float, salida, voz=None, ganancia_db: float = 0.0, max_10s: float | None = None, variantes=None) -> dict:
    """Con voz: voz + efectos a −14 LUFS. Sin voz: efectos solos a −16 LUFS. Escribe <salida>.json con el informe."""
    salida = Path(salida)
    max_10s = max_10s or (8.0 if voz else 16.0)          # con voz, poco; motion sin voz, más denso
    v = OV.leer(Path(voz)) if voz else None
    cama, hechos = disenar(eventos, dur, v, ganancia_db, variantes)
    crudo = salida.with_suffix(".capa.wav")
    with wave.open(str(crudo), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(cama, -1, 1) * 32767).astype("<i2").tobytes())
    mezcla = salida.with_suffix(".premaster.wav")
    if voz:
        subprocess.run([FF, "-v", "error", "-y", "-i", str(voz), "-i", str(crudo), "-filter_complex",
                        "[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0[v];[v][1:a]amix=inputs=2:normalize=0:duration=first[a]",
                        "-map", "[a]", "-c:a", "pcm_s24le", str(mezcla)], check=True)
    else:
        shutil.copy(crudo, mezcla)
    objetivo = -14.0 if voz else -16.0
    medido, _ = _lufs(mezcla)
    subprocess.run([FF, "-v", "error", "-y", "-i", str(mezcla), "-af",
                    f"atrim=0:{dur:.3f},volume={objetivo - medido:.2f}dB,aresample=192000,"
                    "alimiter=limit=0.84:attack=1:release=60:level=false,aresample=48000",
                    "-c:a", "pcm_s24le", str(salida)], check=True)
    mezcla.unlink()
    r = informe(hechos, dur, salida, max_10s)
    salida.with_suffix(".json").write_text(json.dumps(dict(informe=r, efectos=hechos), ensure_ascii=False, indent=1))
    print(f"[sonido] {r['efectos']} efectos · {r['por_10s']}/10 s · {r['tomas_distintas']} tomas · {r['sobre_voz']} sobre la voz · "
          f"{r.get('lufs')} LUFS · pico {r.get('pico_real')} dBTP" + (f" · ⚠ {'; '.join(r['avisos'])}" if r["avisos"] else ""))
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("tomas"); a1.add_argument("papel")
    a2 = sub.add_parser("mezclar"); a2.add_argument("eventos"); a2.add_argument("--dur", type=float, required=True)
    a2.add_argument("--salida", required=True); a2.add_argument("--voz"); a2.add_argument("--ganancia", type=float, default=0.0)
    a2.add_argument("--max-10s", type=float, default=None)
    a = ap.parse_args()
    if a.cmd == "tomas":
        for t in tomas(a.papel):
            print(f"{t['fuente']:9} {round(_centroide(t['x'])):5} Hz  {t['id']}")
    else:
        ev = [(float(e[0]), e[1], e[2] if len(e) > 2 else {}) for e in json.load(open(a.eventos))]
        mezclar(ev, a.dur, a.salida, a.voz, a.ganancia, a.max_10s)
