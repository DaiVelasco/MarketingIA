"""Ejecutar desde la raíz con python -m unittest discover -s pruebas."""
import datetime as dt
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import campana
import instagram


class MetaSimulada:
    identity = instagram.Meta.identity
    account = "100"

    def __init__(self):
        self.username = "cuenta.demo"
        self.owner = self.account
        self.posts = []
        self.uploads = []
        self.responses = []
        self.status = {}
        self.interrupt = False

    def api(self, path, params=None, post=False, discovery=False):
        if post:
            self.posts.append((path, params.copy()))
            remote = str(1000 + len(self.posts))
            if path.endswith("/replies"):
                self.responses.append({"from": {"username": self.username}, "id": remote})
            if self.interrupt and (path.endswith("/media_publish") or path.endswith("/replies")):
                raise TimeoutError("Respuesta remota perdida")
            return {"id": remote}
        if path == self.account:
            return {"id": self.account, "username": self.username}
        if path == "20":
            return {"owner": {"id": self.owner}, "media_type": "CAROUSEL_ALBUM"}
        return {"status_code": self.status.get(path, "FINISHED")}

    def upload(self, container, asset):
        self.uploads.append((container, asset.read_bytes()))

    def pages(self, path, fields):
        if path == "20/comments":
            return [{"id": "30", "from": {"username": "visita"}}]
        if path == "30/replies":
            return self.responses
        raise AssertionError(path)


class OperacionesInstagram(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.cfg = {"modo": "produccion", "cuenta": "cuenta.demo", "zona": "America/Caracas",
                    "referencias": [], "base_imagenes_https": "https://imagenes.example/campanas",
                    "acciones_habilitadas": ["publicar", "publicar-carrusel", "responder"]}
        self.day = "2026-11-21"
        self.meta = MetaSimulada()
        self.reel = self.root / campana.VIDEO / "03 - Videos terminados" / "01 - Reel.mp4"
        self.reel.parent.mkdir(parents=True)
        self.reel.write_bytes(b"video de ensayo")
        self.caption = self.root / "caption.txt"
        self.caption.write_text("Escribe INFO", encoding="utf-8")
        self.make_production_record()
        self.delivery = self.root / "entrega"
        directory = self.delivery / "publicar/carrusel"
        directory.mkdir(parents=True)
        self.images = [directory / f"{n:02}.jpg" for n in range(1, 5)]
        for img in self.images:
            img.write_bytes(img.name.encode())
        (directory.parent / "pie-de-foto.txt").write_text("Texto para carrusel", encoding="utf-8")
        self.remote = {campana.sha256(img): img.read_bytes() for img in self.images}
        self.outbox = self.root / "static"
        self.outbox.mkdir()
        self.qa_reel = self.qa("reel")
        self.qa_carousel = self.qa("carrusel")
        self.publish = ["publicar", self.day, self.reel, self.caption, self.qa_reel]
        self.carousel = ["publicar-carrusel", self.day, self.delivery, self.qa_carousel]
        self.reply = ["responder", "20", "30", self.caption]
        for context in (
            patch.object(instagram, "ROOT", self.root),
            patch.object(instagram, "cfg", return_value=self.cfg),
            patch.object(instagram, "Meta", return_value=self.meta),
            patch.object(instagram, "local_day", return_value=dt.date.fromisoformat(self.day)),
            patch.dict(os.environ, {"MARKETINGIA_MEDIA_OUTBOX": str(self.outbox)}),
            patch("urllib.request.urlopen", side_effect=self.fetch_image),
        ):
            self.enterContext(context)

    def fetch_image(self, url, timeout):
        self.assertTrue(url.startswith(self.cfg["base_imagenes_https"] + "/"))
        return io.BytesIO(self.remote[Path(url).stem])

    def make_production_record(self):
        from herramientas.edicion_reel import HERRAMIENTAS, TRASPASOS
        script = self.root / "guion/montaje-reel-01.json"
        script.parent.mkdir()
        orders = [{"id": t, "herramienta": t, "entrada": 0, "salida": 2,
                   "instruccion": "Aplicar", "insumo": "Material de prueba", "resultado": "Salida simulada"}
                  for t in HERRAMIENTAS]
        script.write_text(json.dumps({"duracion": 2, "ordenes": orders}), encoding="utf-8")
        (self.root / "revision").mkdir()
        self.provenance = self.root / "revision/edicion-reel-01.json"
        self.proof = self.root / "revision/resumen.txt"
        self.proof.write_text("Prueba local de integración", encoding="utf-8")
        evidence = self.proof.relative_to(self.root).as_posix()
        data = {"video": self.reel.relative_to(self.root).as_posix(), "video_sha256": campana.sha256(self.reel),
                "orden_sha256": campana.sha256(script), "traspasos": dict.fromkeys(TRASPASOS, evidence),
                "herramientas": {t: {"estado": "reutilizada", "uso": "Actividad simulada",
                                     "evidencia": evidence, "ordenes": [t]} for t in HERRAMIENTAS}}
        self.provenance.write_text(json.dumps(data), encoding="utf-8")

    def qa(self, kind):
        target = self.root / (kind + ".json")
        if kind == "reel":
            data = campana.review(self.cfg["cuenta"], self.day, kind, self.reel, self.caption)
        else:
            data = campana.review(self.cfg["cuenta"], self.day, kind, self.delivery)
        data["aprobado"] = True
        target.write_text(json.dumps(data), encoding="utf-8")
        return target

    def command(self, args):
        with patch.object(sys, "argv", ["instagram.py", *map(str, args)]):
            return instagram.main()

    def test_ensayo_y_acciones_por_separado(self):
        self.cfg["modo"] = "ensayo"
        for command in (self.publish, self.carousel, self.reply):
            with self.assertRaises(ValueError):
                self.command(command)
        self.cfg["modo"] = "produccion"
        self.cfg["acciones_habilitadas"] = ["responder"]
        with self.assertRaises(ValueError):
            self.command(self.publish)
        self.assertEqual(self.meta.posts, [])
        self.assertEqual(list(self.outbox.iterdir()), [])

    def test_cuenta_del_token_y_cuenta_de_revision(self):
        self.meta.username = "cuenta_equivocada"
        with self.assertRaisesRegex(ValueError, "nombre"):
            self.command(self.publish)
        self.meta.username = self.cfg["cuenta"]
        doc = json.loads(self.qa_reel.read_text())
        doc["cuenta"] = "otro"
        self.qa_reel.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, "QA"):
            self.command(self.publish)
        self.assertEqual(self.meta.posts, [])

    def test_fecha_local_y_archivos_modificados(self):
        with self.assertRaisesRegex(ValueError, "fecha local"):
            self.command(["publicar", "2026-11-20", *self.publish[2:]])
        self.caption.write_text("Otra propuesta.")
        with self.assertRaisesRegex(ValueError, "QA"):
            self.command(self.publish)
        self.images[0].write_bytes(self.images[1].read_bytes())
        with self.assertRaisesRegex(ValueError, "QA"):
            self.command(self.carousel)
        self.assertEqual(self.meta.posts, [])

    def test_reel_sin_traspaso_o_con_evidencia_modificada(self):
        self.proof.write_text("El revisor pidió otra toma", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "QA"):
            self.command(self.publish)
        self.provenance.unlink()
        with self.assertRaisesRegex(ValueError, "edicion-reel"):
            self.command(self.publish)
        self.assertEqual(self.meta.posts, [])

    def test_reel_con_orden_fuera_de_rango_o_herramienta_pendiente(self):
        data = json.loads(self.provenance.read_text())
        data["herramientas"]["invideo"]["estado"] = "pendiente"
        self.provenance.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "invideo pendiente"):
            self.command(self.publish)
        script = self.root / "guion/montaje-reel-01.json"
        plan = json.loads(script.read_text())
        plan["ordenes"][0]["salida"] = 120
        script.write_text(json.dumps(plan))
        with self.assertRaisesRegex(ValueError, "Tramo fuera"):
            self.command(self.publish)
        self.assertEqual(self.meta.posts, [])

    def test_reel_en_proceso_y_reintento_con_recibo(self):
        self.meta.status["1001"] = "IN_PROGRESS"
        self.assertEqual(self.command(self.publish)["estado"], "procesando")
        self.meta.status.clear()
        receipt = self.command(self.publish)
        self.assertEqual(self.command(self.publish)["media_id"], receipt["media_id"])
        self.assertEqual(len(self.meta.uploads), 1)
        self.assertEqual([route for route, _ in self.meta.posts], ["100/media", "100/media_publish"])
        with self.assertRaisesRegex(ValueError, "pieza distinta"):
            self.command(self.carousel)

    def test_respuesta_de_publicacion_perdida(self):
        self.meta.interrupt = True
        with self.assertRaises(TimeoutError):
            self.command(self.publish)
        self.meta.status["1001"] = "PUBLISHED"
        self.assertEqual(self.command(self.publish)["estado"], "enviando")
        self.assertEqual(len(self.meta.posts), 2)

    def test_carrusel_contenedores_ordenados_y_alojamiento(self):
        self.meta.status["1002"] = "IN_PROGRESS"
        self.assertEqual(self.command(self.carousel)["estado"], "procesando")
        self.assertEqual(len(self.meta.posts), 4)
        self.meta.status.clear()
        result = self.command(self.carousel)
        self.assertEqual(result["estado"], "confirmado")
        self.assertEqual(len(self.meta.posts), 6)
        parent = self.meta.posts[4][1]
        self.assertEqual(parent["children"], "1001,1002,1003,1004")
        staged = [(self.outbox / (campana.sha256(img) + ".jpg")).read_bytes() for img in self.images]
        self.assertEqual(staged, [img.read_bytes() for img in self.images])
        self.assertEqual([item[1]["image_url"].split("/")[-1] for item in self.meta.posts[:4]],
                         [campana.sha256(img) + ".jpg" for img in self.images])
        self.assertEqual(self.command(self.carousel)["media_id"], result["media_id"])
        self.assertEqual(len(self.meta.posts), 6)

    def test_alojamiento_con_otra_imagen(self):
        self.remote[campana.sha256(self.images[0])] = b"otra foto"
        with self.assertRaisesRegex(ValueError, "JPG remoto"):
            self.command(self.carousel)
        self.assertEqual(self.meta.posts, [])

    def test_respuestas_y_reconciliacion(self):
        self.meta.owner = "999"
        with self.assertRaisesRegex(ValueError, "cuenta configurada"):
            self.command(self.reply)
        self.meta.owner = self.meta.account
        self.meta.interrupt = True
        with self.assertRaises(TimeoutError):
            self.command(self.reply)
        self.assertEqual(self.command(self.reply)["estado"], "ya_atendido")
        self.assertEqual(self.command(self.reply)["estado"], "confirmado")
        self.assertEqual(len(self.meta.posts), 1)


if __name__ == "__main__":
    unittest.main()
