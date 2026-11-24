"""Abre una campaña local y prepara la ficha de revisión de sus archivos finales."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from herramientas.edicion_reel import (VIDEO, comprobar_reproduccion, expediente,
                                      orden_montaje, sha256, ultima_revision)
from herramientas.orden_carrusel import orden_carrusel

ROOT = Path(__file__).resolve().parent


def cfg():
    with (ROOT / "operacion.toml").open("rb") as f:
        return tomllib.load(f)


def local_day(zone):
    try:
        tz = ZoneInfo(zone)
    except ZoneInfoNotFoundError:
        if zone != "America/Caracas":
            raise ValueError("Instala tzdata para la zona seleccionada.") from None
        tz = dt.timezone(dt.timedelta(hours=-4))
    return dt.datetime.now(tz).date()


def account_name(value):
    value = value.strip()
    if "://" in value:
        url = urlsplit(value)
        if url.hostname not in {"instagram.com", "www.instagram.com"}:
            raise ValueError("Indica el enlace al perfil de Instagram.")
        value = url.path.strip("/")
    value = value.removeprefix("@").lower()
    if not re.fullmatch(r"[a-z0-9_][a-z0-9._]{0,29}", value) or value.endswith("."):
        raise ValueError("Nombre de cuenta no válido.")
    if Path(value).is_reserved():
        raise ValueError("Ese nombre no se puede usar como carpeta portable.")
    return value


def start(root, account, day):
    folder = root / "campanas" / account / day
    for part in (f"{VIDEO}/01 - Videos crudos", f"{VIDEO}/02 - Referencias",
                 f"{VIDEO}/03 - Videos terminados", "guion", "carrusel/arte", "revision"):
        (folder / part).mkdir(parents=True, exist_ok=True)
    brief = folder / "brief.md"
    try:
        with brief.open("x", encoding="utf-8") as file:
            file.write(f"# Campaña de @{account} · {day}\n\n"
                       "| Decisión | Acuerdo del equipo |\n| --- | --- |\n"
                       "| Objetivo principal e indicador observable | |\n"
                       "| Audiencia y pregunta del cliente | |\n"
                       "| Evidencia, fuente, fecha y vigencia | |\n"
                       "| Hipótesis y variable que probaremos | |\n"
                       "| Formatos a producir y pieza elegida para el feed | |\n"
                       "| CTA, destino y responsable de atenderlo | |\n"
                       "| Material autorizado y límites de gasto | |\n"
                       "| Responsable, próximo paso y pendientes | |\n"
                       "| Fecha de publicación, ID y lecturas a 24 h, 72 h y 7 días | |\n")
    except FileExistsError:
        pass
    return folder


def carousel_files(delivery):
    folder = delivery / "publicar"
    images = [folder / "carrusel" / f"{i:02}.jpg" for i in range(1, 5)]
    if set(images) != set((folder / "carrusel").glob("*.jpg")):
        raise ValueError("Usa la entrega exportada con los cuatro JPG numerados del 01 al 04.")
    return images, folder / "pie-de-foto.txt"


def review(account, day, kind, asset, caption=None):
    record = {"cuenta": account, "fecha": day, "formato": kind, "aprobado": False}
    if kind == "reel":
        if not caption or asset.suffix.lower() != ".mp4":
            raise ValueError("Indica el MP4 y su archivo de caption.")
        asset = asset.resolve()
        match = re.match(r"^(\d+)\s*[-_]", asset.name)
        if not match or asset.parent.name != "03 - Videos terminados" or asset.parent.parent.name != VIDEO:
            raise ValueError("La ficha QA de reel requiere el MP4 numerado en 03 - Videos terminados.")
        checked = expediente(asset.parents[2], int(match.group(1)))
        if Path(checked["archivo"]) != asset:
            raise ValueError("El MP4 no corresponde al máster indicado por el expediente QA.")
        record.update({k: checked[k] for k in ("video_sha256", "edicion_sha256")})
    else:
        if caption:
            raise ValueError("El carrusel usa el caption de su propia entrega.")
        images, caption = carousel_files(asset)
        record["imagenes_sha256"] = [sha256(file) for file in images]
    if not caption.read_text(encoding="utf-8-sig").strip():
        raise ValueError("El caption está vacío.")
    record["caption_sha256"] = sha256(caption)
    return record


def produce(folder, formats, version, ffmpeg, draft=False):
    from montaje import render, source

    if (version is not None and version < 1) or not (folder / "brief.md").is_file():
        raise ValueError("Indica una campaña con brief.md y una revisión mayor que cero.")
    folder = folder.resolve()
    revision = folder / "revision"
    revision.mkdir(exist_ok=True)
    outputs = {}
    for kind in formats:
        number = version
        if kind == "reel" and not draft:
            try:
                checked = expediente(folder, version or ultima_revision(folder))
                comprobar_reproduccion(checked["archivo"], ffmpeg, checked["duracion"], checked.get("cierre_referencia"))
                outputs["reel"] = checked["archivo"]
            except (ValueError, OSError, subprocess.CalledProcessError) as error:
                outputs["reel"] = {"estado": "pendiente_edicion", "motivo": str(error)}
            continue
        if kind == "reel":
            plan_file = folder / "guion/escaleta.json"
            plan = json.loads(plan_file.read_text(encoding="utf-8-sig"))
            caption = folder / "guion/pie-de-foto.txt"
            if not caption.read_text(encoding="utf-8-sig").strip():
                raise ValueError("Falta el texto de publicación del reel.")
            files = [plan_file, caption]
            assets = [shot["archivo"] for shot in plan["escenas"] if shot.get("archivo")]
            if plan.get("audio"):
                assets.append(plan["audio"])
            files.extend(Path(source(plan_file.parent, name)) for name in assets)
        elif kind == "carrusel":
            design = folder / "carrusel"
            files = [design / "pie-de-foto.txt", *sorted(p for p in (design / "arte").rglob("*") if p.is_file())]
            plans = sorted((folder / "guion").glob("carrusel-[0-9]*.json"))
            versions = [int(p.stem.split("-")[-1]) for p in plans if p.stem.split("-")[-1].isdigit()]
            number = version or max(versions, default=1)
            # Permite volver a abrir una entrega histórica con sus fuentes originales.
            historic = revision / f"fuentes-carrusel-{number:02}.json"
            if versions or not historic.is_file():
                checked = orden_carrusel(folder, number)
                files.extend([checked["orden"], *(folder / name for name in checked["imagenes"])])
            elif json.loads(historic.read_text(encoding="utf-8")) != {
                    p.relative_to(folder).as_posix(): sha256(p) for p in files}:
                raise ValueError("Para cambiar un carrusel histórico, crea una orden de revisión nueva.")
        else:
            raise ValueError(f"Formato desconocido: {kind}")

        # Reserva una versión de los originales. Tras una interrupción se puede continuar
        # con esos archivos y una corrección posterior conserva las entregas anteriores.
        label = "borrador" if kind == "reel" else kind
        sources = {Path(os.path.relpath(p, folder)).as_posix(): sha256(p) for p in files}
        if number is None:
            prior = [int(p.stem.rsplit("-", 1)[1]) for p in revision.glob(f"fuentes-{label}-*.json")
                     if p.stem.rsplit("-", 1)[1].isdigit()]
            number = max(prior, default=1)
            latest = revision / f"fuentes-{label}-{number:02}.json"
            if latest.exists() and json.loads(latest.read_text(encoding="utf-8")) != sources:
                number += 1
        record = revision / f"fuentes-{label}-{number:02}.json"
        if kind == "reel":
            target = revision / f"borrador-{number:02}.mp4"
        else:
            target = design / ("entrega" if number == 1 else f"entrega-v{number}")
        with tempfile.NamedTemporaryFile(dir=revision, delete=False, mode="w", encoding="utf-8") as f:
            temp = Path(f.name)
            json.dump(sources, f, ensure_ascii=False, indent=2)
        try:
            try:
                os.link(temp, record)
            except FileExistsError:
                if json.loads(record.read_text(encoding="utf-8")) != sources:
                    raise ValueError(f"Los originales de {kind} cambiaron. Usa --revision con un número nuevo.")
        finally:
            temp.unlink()
        if kind == "reel":
            if not ffmpeg:
                raise ValueError("Indica --ffmpeg con su ruta o configura MARKETINGIA_FFMPEG.")
            if target.exists():
                subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-xerror", "-i", str(target),
                                "-map", "0:v", "-map", "0:a?", "-f", "null", "-"], check=True)
            else:
                render(plan_file, target, ffmpeg, temp_parent=revision)
        else:
            subprocess.run(["node", str(ROOT / "herramientas/exportar.cjs"), str(design),
                            "--revision", str(number)], check=True)
        outputs[label] = str(target)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for cmd in ("iniciar", "huellas"):
        p = sub.add_parser(cmd)
        p.add_argument("--cuenta", default=cfg()["cuenta"])
        p.add_argument("--fecha", type=dt.date.fromisoformat, default=local_day(cfg()["zona"]))
        if cmd == "huellas":
            p.add_argument("formato", choices=["reel", "carrusel"])
            p.add_argument("archivo", type=Path, help="MP4 o directorio entrega del exportador")
            p.add_argument("caption", type=Path, nargs="?")
            p.add_argument("--salida", type=Path, help="Ficha nueva para revisión")
    local_ffmpeg = ROOT / ".local/ffmpeg.exe"
    ffmpeg = os.environ.get("MARKETINGIA_FFMPEG") or (str(local_ffmpeg) if local_ffmpeg.is_file() else shutil.which("ffmpeg"))
    for cmd in ("validar-orden", "comprobar-reel", "validar-orden-carrusel"):
        p = sub.add_parser(cmd)
        p.add_argument("carpeta", type=Path)
        p.add_argument("--revision", type=int, required=True)
        if cmd == "comprobar-reel":
            p.add_argument("--ffmpeg", default=ffmpeg)
    p = sub.add_parser("producir", help="Recoger el máster profesional y exportar las piezas gráficas")
    p.add_argument("carpeta", type=Path)
    p.add_argument("--formato", choices=("reel", "carrusel", "ambos"))
    p.add_argument("--revision", type=int, help="Forzar una versión. Por defecto cambia solo si cambian los originales.")
    p.add_argument("--ffmpeg", default=ffmpeg)
    p.add_argument("--borrador", action="store_true", help="Montaje básico local en revision/, para ensayar la escaleta")
    args = parser.parse_args()
    if args.cmd == "validar-orden-carrusel":
        checked = orden_carrusel(args.carpeta, args.revision)
        print(json.dumps(checked, ensure_ascii=False, indent=2, default=str))
        return
    if args.cmd == "validar-orden":
        print(json.dumps(orden_montaje(args.carpeta, args.revision), ensure_ascii=False, indent=2))
        return
    if args.cmd == "comprobar-reel":
        checked = expediente(args.carpeta, args.revision)
        comprobar_reproduccion(checked["archivo"], args.ffmpeg, checked["duracion"], checked.get("cierre_referencia"))
        print(json.dumps(checked, ensure_ascii=False, indent=2))
        return
    if args.cmd == "producir":
        formats = cfg()["formatos"] if args.formato is None else (
            ["reel", "carrusel"] if args.formato == "ambos" else [args.formato])
        result = produce(args.carpeta, formats, args.revision, args.ffmpeg, args.borrador)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if isinstance(result.get("reel"), dict):
            raise SystemExit(2)
        return
    account, day = account_name(args.cuenta), args.fecha.isoformat()
    if args.cmd == "iniciar":
        print(start(ROOT, account, day))
        return
    report = review(account, day, args.formato, args.archivo, args.caption)
    content = json.dumps(report, ensure_ascii=False, indent=2)
    if args.salida:
        with args.salida.open("x", encoding="utf-8") as f:
            f.write(content + "\n")
    print(content)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
