"""Intercambio privado de piezas revisadas y elecciones con un portal externo."""
import argparse
from contextlib import contextmanager
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import sqlite3
from uuid import uuid4
from zipfile import BadZipFile, ZipFile, ZipInfo

from campana import account_name
from herramientas.edicion_reel import local, sha256, texto


def codificar(obj):
    return (json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def objeto(ruta):
    dato = json.loads(ruta.read_text(encoding="utf-8-sig"))
    if not isinstance(dato, dict):
        raise ValueError(f"{ruta.name} debe contener un objeto.")
    return dato


def identidad(carpeta):
    cuenta, jornada = carpeta.parent.name, carpeta.name
    if account_name(cuenta) != cuenta or date.fromisoformat(jornada).isoformat() != jornada:
        raise ValueError("Usa la carpeta de campaña <cuenta>/<AAAA-MM-DD>.")
    return cuenta, jornada


def fuente(carpeta, item, sufijo):
    if not isinstance(item, dict):
        raise ValueError("Cada archivo requiere una ruta y la huella revisada.")
    ruta = local(carpeta, item.get("archivo"))
    if ruta.suffix.lower() != sufijo or sha256(ruta) != item.get("sha256"):
        raise ValueError(f"El formato o la huella revisada cambió en {ruta.name}.")
    return ruta


def directorio_portal(carpeta, ronda=None):
    base = carpeta / "portal"
    if ronda is None:
        return base
    if not isinstance(ronda, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", ronda) or PureWindowsPath(ronda).is_reserved():
        raise ValueError("Usa un slug de ronda de hasta 64 caracteres con letras minúsculas, números, guiones o subrayados.")
    destino = base / ronda
    if destino.resolve() != base.resolve() / ronda:
        raise ValueError("La ronda debe estar directamente dentro de la carpeta portal.")
    return destino


def catalogo(carpeta, ronda=None):
    cuenta, jornada = identidad(carpeta)
    directorio = directorio_portal(carpeta, ronda)
    ficha = objeto(directorio / "catalogo.json")
    if (ficha.get("cuenta"), ficha.get("jornada")) != (cuenta, jornada):
        raise ValueError("El catálogo pertenece a otra campaña.")
    grupo = ficha.get("id")
    if not texto(grupo) or len(grupo) > 160:
        raise ValueError("Indica un id estable para el conjunto de propuestas.")
    # Una decisión se identifica en la memoria por su id de conjunto, incluso entre rondas.
    portal = carpeta / "portal"
    for ruta in [portal / "catalogo.json", *portal.glob("*/catalogo.json")]:
        if ruta.parent == directorio or not ruta.is_file() or not ruta.resolve().is_relative_to(portal.resolve()):
            continue
        try:
            otro = objeto(ruta)
        except (ValueError, UnicodeError):
            continue
        if otro.get("id") == grupo:
            raise ValueError(f"El id de conjunto ya figura en {ruta.relative_to(carpeta)}. Asigna un id distinto a cada ronda.")
    opciones = ficha.get("opciones")
    if not isinstance(opciones, list) or len(opciones) < 2:
        raise ValueError("El administrador necesita al menos dos propuestas.")
    manifiesto = {"version": 1, "id": grupo, "cuenta": cuenta, "jornada": jornada, "opciones": []}
    fuentes, registros = {}, {}
    for op in opciones:
        if not isinstance(op, dict):
            raise ValueError("Cada opción debe contener sus archivos y sus rasgos.")
        clave, formato, version = op.get("id"), op.get("formato"), op.get("version")
        if not isinstance(clave, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", clave) or clave in registros:
            raise ValueError("Usa un id de opción único con letras minúsculas, números, guion o subrayado.")
        if formato not in ("reel", "carrusel") or type(version) is not int or version < 1:
            raise ValueError(f"Revisa el formato y la versión de {clave}.")
        if not texto(op.get("titulo")) or not isinstance(op.get("rasgos"), list) or not op["rasgos"] or not all(map(texto, op["rasgos"])):
            raise ValueError(f"Indica el título y los rasgos observados de {clave}.")
        fuente(carpeta, op.get("revision_editorial"), ".md")
        medios = op.get("archivos")
        cuantos = 1 if formato == "reel" else 4
        if not isinstance(medios, list) or len(medios) != cuantos:
            raise ValueError(f"{clave} necesita {cuantos} archivo(s) en orden.")
        imagenes = []
        for i, item in enumerate(medios, 1):
            ext = ".mp4" if formato == "reel" else ".jpg"
            original = fuente(carpeta, item, ext)
            if formato == "carrusel" and original.name != f"{i:02}.jpg":
                raise ValueError(f"Coloca las láminas de {clave} en su orden de publicación.")
            nombre = f"opciones/{clave}/{i:02}{ext}"
            fuentes[nombre] = original
            imagenes.append({"archivo": nombre, "sha256": item["sha256"]})
        nombre_caption = f"opciones/{clave}/pie-de-foto.txt"
        fuentes[nombre_caption] = fuente(carpeta, op.get("caption"), ".txt")
        if not fuentes[nombre_caption].read_text(encoding="utf-8-sig").strip():
            raise ValueError(f"El pie de foto de {clave} está vacío.")
        huellas = [i["sha256"] for i in medios] + [op["caption"]["sha256"]]
        huella = ":".join((["carrusel"] if formato == "carrusel" else []) + huellas)
        opcion = {k: op[k] for k in ("id", "formato", "version", "titulo", "rasgos")}
        opcion.update(archivos=imagenes, caption={"archivo": nombre_caption, "sha256": huellas[-1]},
                      huella_publicacion=huella)
        manifiesto["opciones"].append(opcion)
        registros[clave] = {"archivos": medios, "caption": op["caption"], "huella_publicacion": huella}
    return manifiesto, fuentes, registros


@contextmanager
def intercambio(carpeta, ronda=None):
    # La reserva SQLite se libera al cerrar incluso si termina el proceso. Serializa
    # regeneración, correcciones y recibo entre los procesos de esta misma campaña.
    directorio = directorio_portal(carpeta, ronda)
    ruta_catalogo = directorio / "catalogo.json"
    if not ruta_catalogo.is_file():
        raise ValueError(f"Falta {ruta_catalogo.relative_to(carpeta)} con las versiones revisadas de la campaña.")
    db = sqlite3.connect(directorio / ".intercambio.sqlite3", timeout=30)
    try:
        db.execute("BEGIN IMMEDIATE")
        yield directorio
    finally:
        db.close()


def preparar(carpeta, ronda=None):
    carpeta = Path(carpeta).resolve()
    with intercambio(carpeta, ronda) as directorio:
        manifiesto, fuentes, _ = catalogo(carpeta, ronda)
        salida = directorio / "propuestas.zip"
        tmp = salida.with_name(f".{uuid4().hex}.tmp")
        try:
            with ZipFile(tmp, "w", allowZip64=True) as z:
                z.writestr(ZipInfo("manifiesto.json"), codificar(manifiesto))
                for nombre, origen in fuentes.items():
                    with origen.open("rb") as src, z.open(ZipInfo(nombre), "w", force_zip64=True) as dst:
                        shutil.copyfileobj(src, dst, 1024 * 1024)
            verificar_zip(tmp, manifiesto)
            os.replace(tmp, salida)
        finally:
            tmp.unlink(missing_ok=True)
    return salida


def verificar_zip(paquete, manifiesto):
    with ZipFile(paquete) as z:
        if z.read("manifiesto.json") != codificar(manifiesto):
            raise ValueError("El paquete y el catálogo revisado difieren. Prepara nuevamente las propuestas.")
        nombres = ["manifiesto.json"]
        for op in manifiesto["opciones"]:
            for item in [*op["archivos"], op["caption"]]:
                nombres.append(item["archivo"])
                with z.open(item["archivo"]) as src:
                    if hashlib.file_digest(src, "sha256").hexdigest() != item["sha256"]:
                        raise ValueError(f"El archivo empaquetado cambió: {item['archivo']}")
        if sorted(z.namelist()) != sorted(nombres):
            raise ValueError("El ZIP contiene entradas adicionales o duplicadas.")


def importar(carpeta, respuesta, *, raiz=None, ronda=None):
    from herramientas.aprendizaje import registrar
    carpeta = Path(carpeta).resolve()
    raiz = Path(raiz).resolve() if raiz is not None else carpeta.parents[2]
    dato = objeto(Path(respuesta))
    with intercambio(carpeta, ronda) as directorio:
        plan, _, referencias = catalogo(carpeta, ronda)
        paquete = directorio / "propuestas.zip"
        sello = sha256(paquete)
        if (dato.get("id"), dato.get("cuenta"), dato.get("paquete_sha256")) != (plan["id"], plan["cuenta"], sello):
            raise ValueError("La elección pertenece a otra cuenta, conjunto o versión del ZIP.")
        verificar_zip(paquete, plan)
        elegida = dato.get("elegida")
        if not isinstance(elegida, str) or elegida not in referencias:
            raise ValueError("La opción elegida no figura en el paquete.")
        if not isinstance(dato.get("fecha"), str) or datetime.fromisoformat(dato["fecha"]).utcoffset() is None:
            raise ValueError("La fecha de la decisión debe incluir la zona horaria.")
        revision, motivo = dato.get("revision"), dato.get("motivo_admin", "")
        if type(revision) is not int or revision < 1 or not isinstance(motivo, str):
            raise ValueError("Indica una revisión positiva y un motivo textual opcional.")
        opciones = [{k: op[k] for k in ("id", "titulo", "formato", "rasgos", "huella_publicacion")}
                    for op in plan["opciones"]]
        seleccion = next(op for op in plan["opciones"] if op["id"] == elegida)
        evento = {"tipo": "decision", "id": plan["id"], "formato": seleccion["formato"],
                  "elegida": elegida, "opciones": opciones, "motivo_admin": motivo, "fecha": dato["fecha"]}
        recibo = {"cuenta": plan["cuenta"], "jornada": plan["jornada"], "revision": revision,
                  "version_pieza": seleccion["version"], "paquete_sha256": sello,
                  **{k: evento[k] for k in ("id", "fecha", "formato", "elegida", "motivo_admin")},
                  **referencias[elegida]}
        destino = directorio / "seleccion.json"
        anterior = objeto(destino) if destino.exists() else None
        if anterior and all(anterior.get(k) == v for k, v in recibo.items()):
            return destino
        if revision != (anterior["revision"] + 1 if anterior else 1):
            raise ValueError("La revisión está desactualizada. Una corrección usa el número siguiente.")
        if anterior and datetime.fromisoformat(dato["fecha"]) < datetime.fromisoformat(anterior["fecha"]):
            raise ValueError("La corrección no puede ser anterior a la elección vigente.")
        tmp = destino.with_name(f".{uuid4().hex}.tmp")
        try:
            evento["si_revision"] = anterior["revision_memoria"] if anterior else 0
            respaldo = registrar(raiz, plan["cuenta"], evento)
            recibo["revision_memoria"] = respaldo["revision"]
            tmp.write_bytes(codificar(recibo))
            os.replace(tmp, destino)
        finally:
            tmp.unlink(missing_ok=True)
    return destino


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="accion", required=True)
    prep = sub.add_parser("preparar")
    impor = sub.add_parser("importar")
    for operacion in (prep, impor):
        operacion.add_argument("carpeta", type=Path)
        operacion.add_argument("--ronda", metavar="SLUG", help="Carpeta de esta ronda dentro de portal, por ejemplo ronda-02.")
    impor.add_argument("respuesta", type=Path)
    args = p.parse_args()
    try:
        archivo = preparar(args.carpeta, args.ronda) if args.accion == "preparar" else importar(args.carpeta, args.respuesta, ronda=args.ronda)
        print(archivo)
        print(f"SHA-256 {sha256(archivo)}")
    except (ValueError, KeyError, OSError, BadZipFile, sqlite3.Error) as e:
        p.exit(1, f"{e}\n")


if __name__ == "__main__":
    main()
