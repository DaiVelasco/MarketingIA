"""Comprueba las órdenes del guionista y las evidencias de la edición profesional."""
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import unicodedata
from urllib.parse import urlsplit


VIDEO = "Videos del proyecto - Reel de Instagram"
HERRAMIENTAS = ("ElevenLabs", "Whisper", "invideo", "HyperFrames", "Remotion",
                "gbro-collage-broll", "ClaudeAnimationBase")
TRASPASOS = ("investigacion", "analitica", "director", "contenidos", "editor_video", "revision")


def sha256(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def texto(value):
    return isinstance(value, str) and bool(value.strip())


def cargar(path):
    if not path.is_file():
        raise ValueError(f"Falta {path.parent.name}/{path.name}.")
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path.name} debe contener un objeto JSON.")
    return obj


def numero(value):
    return type(value) in (int, float) and math.isfinite(value)


def orden_montaje(folder, version):
    if version < 1:
        raise ValueError("La revisión debe ser un número positivo.")
    plan = folder / "guion" / f"montaje-reel-{version:02}.json"
    data = cargar(plan)
    duration, orders = data.get("duracion"), data.get("ordenes")
    if not numero(duration) or duration <= 0 or not isinstance(orders, list):
        raise ValueError("La orden necesita duracion positiva en segundos y una lista de ordenes.")
    assigned = {tool: [] for tool in HERRAMIENTAS}
    ids = set()
    for row in orders:
        if not isinstance(row, dict) or any(not texto(row.get(k)) for k in
                                            ("id", "herramienta", "instruccion", "insumo", "resultado")):
            raise ValueError("Cada orden necesita id, herramienta, instruccion, insumo y resultado.")
        key, tool = row["id"], row["herramienta"]
        if key in ids or tool not in assigned:
            raise ValueError(f"Identificador repetido o herramienta desconocida en {key}.")
        begin, end = row.get("entrada"), row.get("salida")
        if not numero(begin) or not numero(end) or not 0 <= begin < end <= duration:
            raise ValueError(f"Tramo fuera de la duración del guion en {key}.")
        ids.add(key)
        assigned[tool].append(key)
    missing = [tool for tool, rows in assigned.items() if not rows]
    if missing:
        raise ValueError("El guionista debe asignar tramo y operación a " + ", ".join(missing) + ".")
    digest = sha256(plan)
    result = {"orden_sha256": digest, "duracion": duration, "asignacion": assigned}
    contract = data.get("guion_voz")
    if contract is None:
        # Las entregas previas ya revisadas conservan el contrato con el que se aprobaron.
        receipt = folder / "revision" / f"edicion-reel-{version:02}.json"
        if not receipt.is_file() or cargar(receipt).get("orden_sha256") != digest:
            raise ValueError("Falta guion_voz con la locución, los subtítulos y las tomas por frase.")
    else:
        result["subtitulos_sha256"] = validar_guion_voz(folder, version, duration, contract)
    return result


def local(folder, value):
    if not texto(value) or Path(value).is_absolute() or Path(value).drive:
        raise ValueError(f"Indica un archivo relativo a la campaña: {value!r}.")
    path = (folder / value).resolve()
    if not path.is_relative_to(folder.resolve()) or not path.is_file() or not path.stat().st_size:
        raise ValueError(f"Evidencia local ausente o fuera de la campaña: {value!r}.")
    return path


def palabras(text):
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFC", text).casefold())


def leer_subtitulos(path, duration):
    contents = path.read_text(encoding="utf-8-sig").strip()
    cues = []
    timestamp = r"(\d{2}):([0-5]\d):([0-5]\d),(\d{3})"
    for block in re.split(r"\n\s*\n", contents):
        lines = block.splitlines()
        times = re.fullmatch(timestamp + r"\s+-->\s+" + timestamp, lines[1]) if len(lines) >= 3 else None
        if not times or not lines[0].strip().isdigit():
            raise ValueError("Los subtítulos deben ser un SRT con tiempos y texto.")
        h, m, s, ms, h2, m2, s2, ms2 = map(int, times.groups())
        begin = 3600*h + 60*m + s + ms/1000
        end = 3600*h2 + 60*m2 + s2 + ms2/1000
        caption = " ".join(lines[2:]).strip()
        if not caption or not 0 <= begin < end <= duration + 0.001 or (cues and begin < cues[-1][1]):
            raise ValueError("Hay un subtítulo vacío, solapado o fuera del reel.")
        cues.append((begin, end, caption))
    return cues


def validar_guion_voz(folder, version, duration, contract):
    script = folder / "guion" / f"voz-reel-{version:02}.json"
    phrases = cargar(script).get("frases")
    if not isinstance(contract, dict) or not isinstance(phrases, list) or not phrases:
        raise ValueError("Se necesita un guion de voz con frases.")
    if sha256(script) != contract.get("guion_sha256"):
        raise ValueError("El guion cambió después de elegir las tomas.")
    voice = local(folder, contract.get("voz"))
    if sha256(voice) != contract.get("voz_sha256"):
        raise ValueError("La locución cambió. Realinea Whisper y revisa las tomas.")
    srt = local(folder, contract.get("subtitulos"))
    cues = leer_subtitulos(srt, duration)
    targets = {}
    for phrase in phrases:
        if not isinstance(phrase, dict) or not all(texto(phrase.get(k)) for k in ("id","texto","objetivo_visual")):
            raise ValueError("Cada frase necesita un id, su texto literal y un objetivo visual.")
        key = phrase["id"]
        if key in targets:
            raise ValueError(f"Frase duplicada: {key}.")
        targets[key] = phrase["texto"]
    caption_words = [(word, begin, end) for begin, end, line in cues for word in palabras(line)]
    if palabras(" ".join(targets.values())) != [word for word, _, _ in caption_words]:
        raise ValueError("Los subtítulos deben reproducir el texto de todo el guion de voz.")
    spoken = {}
    offset = 0
    for key, line in targets.items():
        tokens = palabras(line)
        if not tokens:
            raise ValueError(f"La frase {key} necesita palabras.")
        spoken[key] = (caption_words[offset][1], caption_words[offset + len(tokens) - 1][2])
        offset += len(tokens)
    shots = contract.get("tomas")
    if not isinstance(shots, list):
        raise ValueError("Falta la selección de tomas por frase.")
    covered = set()
    for shot in shots:
        if not isinstance(shot, dict) or not texto(shot.get("frase")) or shot["frase"] not in targets or not texto(shot.get("motivo")):
            raise ValueError("Cada toma debe explicar qué se ve y a qué frase responde.")
        local(folder, shot.get("archivo"))
        start, end, at, until = (shot.get(k) for k in ("desde", "hasta", "entrada", "salida"))
        if not all(map(numero, (start, end, at, until))) or not (0 <= start < end and 0 <= at < until <= duration + 0.001):
            raise ValueError(f"Tiempos de toma inválidos en {shot['frase']}.")
        first, last = spoken[shot["frase"]]
        if at < last and until > first:
            covered.add(shot["frase"])
    if covered != set(targets):
        raise ValueError("Faltan tomas durante la voz de " + ", ".join(sorted(targets.keys() - covered)) + ".")
    return sha256(srt)


def expediente(folder, version):
    folder = folder.resolve()
    manifest = folder / "revision" / f"edicion-reel-{version:02}.json"
    data = cargar(manifest)
    plan = orden_montaje(folder, version)
    if data.get("orden_sha256") != plan["orden_sha256"]:
        raise ValueError("La hoja de montaje cambió. El director debe conciliar la orden con la edición.")
    handoffs, tools = data.get("traspasos"), data.get("herramientas")
    if not isinstance(handoffs, dict) or not isinstance(tools, dict):
        raise ValueError("El expediente requiere traspasos y herramientas.")
    fingerprints = {"manifiesto": sha256(manifest)}
    if "subtitulos_sha256" in plan:
        fingerprints["srt"] = plan["subtitulos_sha256"]
    for role in TRASPASOS:
        fingerprints[role] = sha256(local(folder, handoffs.get(role)))
    for tool, assigned in plan["asignacion"].items():
        row = tools.get(tool)
        if not isinstance(row, dict) or not texto(row.get("uso")):
            raise ValueError(f"Falta el aporte o el bloqueo de {tool}.")
        if row.get("estado") not in ("ejecutada", "reutilizada"):
            raise ValueError(f"{tool} pendiente. {row['uso']}")
        orders = row.get("ordenes")
        if (not isinstance(orders, list) or not all(texto(x) for x in orders)
                or sorted(orders) != sorted(assigned)):
            raise ValueError(f"Las evidencias de {tool} deben cubrir sus órdenes {', '.join(assigned)}.")
        evidence = row.get("evidencia")
        if texto(evidence) and evidence.startswith("https://"):
            where = urlsplit(evidence)
            if tool != "invideo" or where.hostname not in {"invideo.io", "www.invideo.io", "ai.invideo.io"} or not where.path.strip("/"):
                raise ValueError(f"{tool} requiere evidencia local o un proyecto de invideo con identidad verificable.")
            fingerprints[tool] = evidence
        else:
            fingerprints[tool] = sha256(local(folder, evidence))
    master = local(folder, data.get("video"))
    if (master.parent != folder / VIDEO / "03 - Videos terminados" or master.suffix.lower() != ".mp4"
            or not re.match(rf"^{version:02}\s*[-_]", master.name)):
        raise ValueError("El MP4 debe estar numerado para esta revisión en 03 - Videos terminados.")
    digest = sha256(master)
    if data.get("video_sha256") != digest:
        raise ValueError("La huella del MP4 difiere del expediente de edición.")
    stamp = hashlib.sha256(json.dumps(fingerprints, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return {"archivo": str(master), "video_sha256": digest, "edicion_sha256": stamp, "duracion": plan["duracion"]}


def comprobar_reproduccion(master, ffmpeg, duration):
    if not ffmpeg:
        raise ValueError("Instala FFmpeg o configura MARKETINGIA_FFMPEG para verificar el máster.")
    result = subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-xerror", "-progress", "pipe:1",
                             "-i", str(master), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"],
                            check=True, capture_output=True, text=True)
    times = re.findall(r"^out_time_us=(\d+)$", result.stdout, re.MULTILINE)
    if not times or abs(int(times[-1]) / 1_000_000 - duration) > 0.25:
        raise ValueError("La duración decodificada difiere de la orden del guionista.")


def ultima_revision(folder):
    versions = []
    for part, prefix in (("guion", "montaje-reel-"), ("revision", "edicion-reel-")):
        for path in (folder / part).glob(prefix + "*.json"):
            value = path.stem.removeprefix(prefix)
            if value.isdigit():
                versions.append(int(value))
    return max(versions, default=1)
