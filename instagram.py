"""Adaptador de Instagram para el proyecto. Python 3.11+ y biblioteca estándar."""
import argparse
from contextlib import closing
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from campana import ROOT, cfg, carousel_files, local_day, review, sha256

MEDIA_FIELDS = "id,username,caption,permalink,timestamp,media_product_type,media_type,comments_count,like_count"
COMMENT_FIELDS = "id,from,text,timestamp,hidden"


def numeric(value):
    value = str(value)
    if not re.fullmatch(r"\d+", value):
        raise ValueError("Meta requiere un ID numérico.")
    return value


def request_json(request):
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            err = json.load(exc).get("error", {})
        except (ValueError, AttributeError):
            err = {}
        raise RuntimeError(f"Meta HTTP {exc.code}, código {err.get('code')}, subcódigo {err.get('error_subcode')}. Comprueba los permisos, el recurso y la versión.") from None


class Meta:
    def __init__(self):
        self.account = numeric(os.environ.get("MARKETINGIA_IG_ID", ""))
        self.version = os.environ.get("MARKETINGIA_GRAPH_VERSION", "")
        if not re.fullmatch(r"v\d+\.\d+", self.version):
            raise ValueError("Configura MARKETINGIA_GRAPH_VERSION con una versión habilitada en tu app.")
        self.token = os.environ.get("MARKETINGIA_PAGE_TOKEN", "")
        if not self.token:
            raise ValueError("Falta MARKETINGIA_PAGE_TOKEN.")

    def api(self, path, params=None, post=False, discovery=False):
        needs_user = discovery or path.endswith(("/comments", "/replies", "/insights"))
        token = os.environ.get("MARKETINGIA_DISCOVERY_TOKEN", "") if needs_user else self.token
        if not token:
            raise ValueError("Falta MARKETINGIA_DISCOVERY_TOKEN, el token de usuario de Facebook para esta operación.")
        url = f"https://graph.facebook.com/{self.version}/{path}"
        body = urllib.parse.urlencode(params or {}).encode()
        if not post and body:
            url += "?" + body.decode()
        req = urllib.request.Request(url, data=body if post else None, headers={"Authorization": "Bearer " + token})
        return request_json(req)

    def iter_rows(self, path, fields, max_rows=None, page_size=50):
        """Lee por demanda y acota el tamaño de la última petición cuando hay tope."""
        if not 1 <= page_size <= 50 or (max_rows is not None and max_rows < 1):
            raise ValueError("Tamaño o tope de paginación no válido.")
        params = {"fields": fields}
        emitted = 0
        seen = set()
        while True:
            params["limit"] = page_size if max_rows is None else min(page_size,max_rows-emitted)
            result = self.api(path, params)
            for item in result["data"]:
                emitted += 1
                yield item
                if max_rows is not None and emitted >= max_rows:
                    return
            paging = result.get("paging", {})
            if not paging.get("next"):
                return
            cursor = paging.get("cursors", {}).get("after")
            if not cursor or cursor in seen:
                raise ValueError("Paginación incompleta. Conserva el último registro válido.")
            seen.add(cursor)
            params["after"] = cursor

    def pages(self, path, fields):
        return list(self.iter_rows(path, fields))

    def identity(self, config):
        identity = self.api(self.account, {"fields": "id,username"})
        if identity.get("id") != self.account or str(identity.get("username", "")).casefold() != config["cuenta"].casefold():
            raise ValueError("El ID o el nombre devuelto por Meta difiere de operacion.toml.")
        return identity

    def upload(self, container, video):
        url = f"https://rupload.facebook.com/ig-api-upload/{self.version}/{numeric(container)}"
        size = str(video.stat().st_size)
        headers = {"Authorization": "OAuth " + self.token, "offset": "0", "file_size": size,
                   "Content-Length": size, "Content-Type": "application/octet-stream"}
        with video.open("rb") as stream:
            result = request_json(urllib.request.Request(url, data=stream, headers=headers, method="POST"))
        if not result.get("success"):
            raise ValueError("Meta no confirmó la carga del MP4.")


def ledger():
    folder = ROOT / "estado"
    folder.mkdir(exist_ok=True)
    db = sqlite3.connect(folder / "acciones.sqlite", timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS acciones (clave TEXT PRIMARY KEY, huella TEXT NOT NULL, estado TEXT NOT NULL, contenedor TEXT, remoto TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS laminas (clave TEXT, posicion INTEGER, contenedor TEXT NOT NULL, PRIMARY KEY(clave,posicion))")
    return db


def reserve(db, key, digest):
    with db:
        db.execute("INSERT OR IGNORE INTO acciones (clave,huella,estado) VALUES (?,?,'nuevo')", (key, digest))
        saved = db.execute("SELECT huella,estado,contenedor,remoto FROM acciones WHERE clave=?", (key,)).fetchone()
    if saved[0] != digest:
        raise ValueError("Ya existe otra versión para esa cuenta y clave. Revisa el historial.")
    return saved[1:]


def move(db, key, before, after, container=None, remote=None):
    with db:
        changed = db.execute("UPDATE acciones SET estado=?,contenedor=COALESCE(?,contenedor),remoto=COALESCE(?,remoto) WHERE clave=? AND estado=?",
                             (after, container, remote, key, before)).rowcount
    if not changed:
        raise ValueError("Otra ejecución ha avanzado esta operación. Consulta registro.")


def supported(item):
    return item.get("media_product_type") == "REELS" or item.get("media_type") == "CAROUSEL_ALBUM"


def image_urls(config, images, hashes):
    base = config.get("base_imagenes_https", "").rstrip("/")
    url = urllib.parse.urlsplit(base)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("Configura base_imagenes_https con el directorio público de JPG de la marca.")
    urls = []
    outbox = os.environ.get("MARKETINGIA_MEDIA_OUTBOX")
    if outbox and not Path(outbox).is_dir():
        raise ValueError("MARKETINGIA_MEDIA_OUTBOX debe apuntar al directorio del alojamiento de la marca.")
    for image, digest in zip(images, hashes, strict=True):
        address = f"{base}/{digest}.jpg"
        if outbox:
            destination = Path(outbox) / f"{digest}.jpg"
            if destination.is_file():
                if sha256(destination) != digest:
                    raise ValueError("El archivo del alojamiento tiene una huella distinta de su nombre.")
            else:
                data = image.read_bytes()
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError(f"La lámina {image.name} cambió después de la revisión.")
                with tempfile.NamedTemporaryFile(dir=outbox, delete=False) as tmp:
                    temporary = Path(tmp.name)
                try:
                    temporary.write_bytes(data)
                    os.replace(temporary, destination)
                finally:
                    temporary.unlink(missing_ok=True)
        with urllib.request.urlopen(address, timeout=30) as response:
            data = response.read(image.stat().st_size + 1)
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"El JPG remoto difiere de la lámina {image.name}.")
        urls.append(address)
    return urls


def carousel_container(meta, db, key, urls, caption):
    children = []
    for position, url in enumerate(urls):
        row = db.execute("SELECT contenedor FROM laminas WHERE clave=? AND posicion=?", (key, position)).fetchone()
        if not row:
            item = meta.api(meta.account + "/media", {"image_url": url, "is_carousel_item": "true"}, post=True)
            with db:
                db.execute("INSERT OR IGNORE INTO laminas VALUES (?,?,?)", (key, position, numeric(item["id"])))
                row = db.execute("SELECT contenedor FROM laminas WHERE clave=? AND posicion=?", (key, position)).fetchone()
        children.append(row[0])
    for child in children:
        status = meta.api(child, {"fields": "status_code"})["status_code"]
        if status != "FINISHED":
            return None, processing_status(child, status)
    result = meta.api(meta.account + "/media", {"media_type": "CAROUSEL", "children": ",".join(children),
                      "caption": caption}, post=True)
    return numeric(result["id"]), None


def processing_status(container, status):
    state = "procesando" if status == "IN_PROGRESS" else "revisar"
    return {"estado": state, "contenedor": container, "meta": status}


def publish(meta, db, args, config):
    kind = "reel" if args.cmd == "publicar" else "carrusel"
    asset = Path(args.video if kind == "reel" else args.entrega)
    caption = Path(args.caption) if kind == "reel" else None
    qa = json.loads(Path(args.qa).read_text(encoding="utf-8-sig"))
    day = dt.date.fromisoformat(args.fecha).isoformat()
    if day != local_day(config["zona"]).isoformat():
        raise ValueError("El envío corresponde a otra fecha local. Consulta registro.")
    expected = review(config["cuenta"], day, kind, asset, caption)
    expected["aprobado"] = True
    if qa.get("aprobado") is not True or any(qa.get(k) != v for k, v in expected.items()):
        raise ValueError("Revisa la cuenta, fecha, formato, orden, archivos y caption de la ficha QA.")
    # La clave antigua sigue protegiendo jornadas importadas de la instalación de reels.
    legacy = f"{meta.account}:reel:{day}"
    existing = db.execute("SELECT 1 FROM acciones WHERE clave=?", (legacy,)).fetchone()
    key = legacy if existing else f"{meta.account}:feed:{day}"
    if kind == "reel":
        digest = qa["video_sha256"] + ":" + qa["caption_sha256"]
    else:
        images, caption = carousel_files(asset)
        digest = ":".join(["carrusel", *qa["imagenes_sha256"], qa["caption_sha256"]])
    text = caption.read_text(encoding="utf-8-sig").strip()
    saved = db.execute("SELECT huella,estado,contenedor,remoto FROM acciones WHERE clave=?", (key,)).fetchone()
    if saved and saved[0] != digest:
        raise ValueError("Ya existe una pieza distinta para el feed de esa fecha. Consulta registro.")
    urls = None
    if kind == "carrusel" and (not saved or saved[1] == "nuevo"):
        urls = image_urls(config, images, qa["imagenes_sha256"])
    stage, container, remote = reserve(db, key, digest)
    if stage == "confirmado":
        return {"estado": stage, "media_id": remote}
    if stage == "nuevo" and kind == "carrusel":
        container, waiting = carousel_container(meta, db, key, urls, text)
        if waiting:
            return waiting
        move(db, key, "nuevo", "procesando", container=container)
        stage = "procesando"
    elif stage == "nuevo":
        result = meta.api(meta.account + "/media", {"media_type": "REELS", "upload_type": "resumable",
                          "caption": text}, post=True)
        container = numeric(result["id"])
        move(db, key, "nuevo", "cargando", container=container)
        meta.upload(container, asset)
        move(db, key, "cargando", "procesando")
        stage = "procesando"
    if stage in ("cargando", "enviando"):
        status = meta.api(numeric(container), {"fields": "status_code"})
        if stage == "cargando" and status.get("status_code") == "FINISHED":
            move(db, key, "cargando", "procesando")
            stage = "procesando"
        else:
            return {"estado": stage, "contenedor": container, "meta": status, "accion": "Conciliar antes de repetir una escritura."}
    status = meta.api(numeric(container), {"fields": "status_code"})["status_code"]
    if status != "FINISHED":
        return processing_status(container, status)
    move(db, key, "procesando", "enviando")
    result = meta.api(meta.account + "/media_publish", {"creation_id": container}, post=True)
    remote = numeric(result["id"])
    move(db, key, "enviando", "confirmado", remote=remote)
    return {"estado": "confirmado", "media_id": remote, "contenedor": container}


def reply(meta, db, args, username):
    media, comment = numeric(args.medio), numeric(args.comentario)
    owner = meta.api(media, {"fields": "owner,media_product_type,media_type"})
    if owner.get("owner", {}).get("id") != meta.account or not supported(owner):
        raise ValueError("Selecciona un reel o carrusel de la cuenta configurada.")
    item = next((row for row in meta.pages(media + "/comments", COMMENT_FIELDS) if row.get("id") == comment), None)
    author = ((item or {}).get("from") or {}).get("username")
    if not author or item.get("hidden") or author.casefold() == username.casefold():
        raise ValueError("Solo se atienden comentarios principales, visibles y ajenos en el medio indicado.")
    message = Path(args.texto).read_text(encoding="utf-8-sig").strip()
    if not message:
        raise ValueError("Respuesta vacía.")
    key = f"{meta.account}:comentario:{comment}"
    stage, _, remote = reserve(db, key, hashlib.sha256(message.encode()).hexdigest())
    if stage == "confirmado":
        return {"estado": stage, "respuesta_id": remote}
    for earlier in meta.pages(comment + "/replies", COMMENT_FIELDS):
        earlier_author = (earlier.get("from") or {}).get("username")
        if not earlier_author:
            raise ValueError("Falta el autor de una respuesta previa. Revisa el hilo para evitar duplicados.")
        if earlier_author.casefold() == username.casefold():
            move(db, key, stage, "confirmado", remote=numeric(earlier["id"]))
            return {"estado": "ya_atendido", "respuesta_id": earlier["id"]}
    if stage != "nuevo":
        return {"estado": stage, "accion": "Verifica la conversación antes de repetir el envío."}
    move(db, key, "nuevo", "enviando")
    result = meta.api(comment + "/replies", {"message": message}, post=True)
    remote = numeric(result["id"])
    move(db, key, "enviando", "confirmado", remote=remote)
    return {"estado": "confirmado", "respuesta_id": remote}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("diagnostico", "cuenta", "registro"):
        sub.add_parser(name)
    sub.add_parser("propios").add_argument("--formato", choices=("reel", "carrusel", "todos"), default="reel")
    sub.add_parser("referencia").add_argument("usuario")
    for name in ("metricas", "comentarios"):
        sub.add_parser(name).add_argument("medio")
    p = sub.add_parser("publicar")
    for field in ("fecha", "video", "caption", "qa"):
        p.add_argument(field)
    p = sub.add_parser("publicar-carrusel")
    for field in ("fecha", "entrega", "qa"):
        p.add_argument(field)
    p = sub.add_parser("responder")
    for field in ("medio", "comentario", "texto"):
        p.add_argument(field)
    args = parser.parse_args()
    config = cfg()
    if args.cmd == "diagnostico":
        variables = ("MARKETINGIA_IG_ID", "MARKETINGIA_GRAPH_VERSION", "MARKETINGIA_PAGE_TOKEN", "MARKETINGIA_DISCOVERY_TOKEN", "MARKETINGIA_MEDIA_OUTBOX")
        return {"cuenta": config["cuenta"], "modo": config["modo"], "referencias": config["referencias"],
                "acciones_habilitadas": config.get("acciones_habilitadas", []),
                "alojamiento_carrusel_configurado": bool(config.get("base_imagenes_https")),
                "variables_presentes": {key: bool(os.environ.get(key)) for key in variables}}
    if args.cmd == "registro":
        with closing(ledger()) as db:
            return list(db.execute("SELECT clave,estado,contenedor,remoto FROM acciones ORDER BY rowid DESC"))
    if args.cmd in ("publicar", "publicar-carrusel", "responder"):
        if config["modo"] != "produccion" or args.cmd not in config.get("acciones_habilitadas", []):
            raise ValueError("La operación requiere producción y esa acción habilitada en operacion.toml.")
    meta = Meta()
    identity = meta.identity(config)
    if args.cmd == "cuenta":
        return identity
    if args.cmd == "propios":
        rows = meta.pages(meta.account + "/media", MEDIA_FIELDS)
        if args.formato == "todos":
            return [r for r in rows if supported(r)]
        if args.formato == "carrusel":
            return [r for r in rows if r.get("media_type") == "CAROUSEL_ALBUM"]
        return [r for r in rows if r.get("media_product_type") == "REELS"]
    if args.cmd == "referencia":
        user = args.usuario.lstrip("@").lower()
        if not re.fullmatch(r"[a-z0-9_.]{1,30}", user) or user not in [x.lower().lstrip("@") for x in config["referencias"]]:
            raise ValueError("El usuario debe figurar en referencias de operacion.toml.")
        # One recent window per run; the director persists daily snapshots.
        fields = f"business_discovery.username({user}){{username,media.limit(50){{{MEDIA_FIELDS},view_count}}}}"
        return meta.api(meta.account, {"fields": fields}, discovery=True).get("business_discovery", {})
    if args.cmd == "metricas":
        return meta.api(numeric(args.medio) + "/insights", {"metric": "views,reach,saved,shares"})
    if args.cmd == "comentarios":
        return meta.pages(numeric(args.medio) + "/comments", COMMENT_FIELDS)
    with closing(ledger()) as db:
        if args.cmd in ("publicar", "publicar-carrusel"):
            return publish(meta, db, args, config)
        return reply(meta, db, args, identity["username"])


if __name__ == "__main__":
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, RuntimeError, sqlite3.Error) as error:
        sys.exit(str(error))
