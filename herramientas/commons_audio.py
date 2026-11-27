"""Importa un sonido identificado por su ficha pública de Wikimedia Commons."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request


def importar(titulo, banco):
    titulo = titulo.removeprefix("File:").strip()
    params = dict(action="query", titles=f"File:{titulo}", prop="imageinfo", redirects=1,
                  iiprop="url|size|mime|sha1|extmetadata", format="json", formatversion=2,
                  iiextmetadatafilter="LicenseShortName|LicenseUrl|Artist")
    headers = {"User-Agent": "MarketingIA/1.0 (Wikimedia Commons sound editor)"}
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params),
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        pages = json.load(response)["query"]["pages"]
    if not pages or not pages[0].get("imageinfo"):
        raise ValueError(f"Commons no encontró la ficha de audio «{titulo}».")
    page = pages[0]
    info = page["imageinfo"][0]
    meta = info["extmetadata"]
    license_name = meta.get("LicenseShortName", {}).get("value", "")
    if not re.fullmatch(r"Public domain|CC0(?: 1\.0)?|CC BY \d+\.\d+", license_name):
        raise ValueError(f"Licencia fuera de la selección del editor: {license_name or 'sin identificar'}.")
    url = urllib.parse.urlsplit(info["url"])
    if url.scheme != "https" or url.hostname != "upload.wikimedia.org":
        raise ValueError("La ficha no apunta al servidor de archivos de Wikimedia Commons.")
    if not (info["mime"].startswith("audio/") or info["mime"] == "application/ogg"):
        raise ValueError("El archivo de Commons no está catalogado como audio.")
    filename = re.sub(r"[^\w.()-]+", "_", page["title"].removeprefix("File:")).strip(".")
    if not filename:
        raise ValueError("La ficha no contiene un nombre de archivo utilizable.")
    folder = banco / "grabaciones" / "commons"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / filename
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        temp = Path(tmp)
        audio = target if target.exists() else temp / "audio"
        if audio != target:
            req = urllib.request.Request(info["url"], headers=headers)
            with urllib.request.urlopen(req, timeout=60) as response, audio.open("wb") as out:
                shutil.copyfileobj(response, out)
        with audio.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha1").hexdigest()
        if digest != info["sha1"] or audio.stat().st_size != info["size"]:
            raise ValueError("El sonido no coincide en tamaño y huella con la ficha de Commons.")
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type:format=duration",
                                 "-of", "json", str(audio)], capture_output=True, text=True, check=True)
        probe = json.loads(result.stdout)
        if not any(s["codec_type"] == "audio" for s in probe["streams"]):
            raise ValueError("FFprobe no identificó una pista de audio.")
        autor = html.unescape(re.sub("<[^>]*>", "", meta.get("Artist", {}).get("value", ""))).strip()
        license_url = meta.get("LicenseUrl", {}).get("value", "")
        if license_name.startswith("CC BY") and not (autor and license_url):
            raise ValueError("A la ficha CC BY le faltan datos para atribuir el recurso.")
        ficha = dict(titulo=page["title"], archivo=filename, fuente="Wikimedia Commons", autor=autor,
                     licencia=license_name, enlace_licencia=license_url, ficha=info["descriptionurl"], sha1=digest,
                     modificaciones="Ninguna", duracion=float(probe["format"]["duration"]))
        creditos = temp / "fuente.json"
        creditos.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
        if audio != target:
            audio.replace(target)
        creditos.replace(target.with_suffix(target.suffix + ".fuente.json"))
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("titulo", help='Por ejemplo "File:Holga shuttersound.ogg"')
    args = parser.parse_args()
    try:
        print(importar(args.titulo, Path(os.environ.get("SONIDOS_DIR", "sonidos")).resolve()))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Wikimedia Commons: {error}\n")
