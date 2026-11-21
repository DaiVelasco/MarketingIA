import json
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import biblioteca as lib


class Biblioteca(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.db = self.enterContext(closing(lib.abrir(self.root)))
        video = self.root / "campanas/cuenta.demo/2026-11-21" / lib.VIDEO
        self.refs = video / "02 - Referencias"
        self.refs.mkdir(parents=True)
        (video / "01 - Videos crudos").mkdir()
        (video / "03 - Videos terminados").mkdir()
        self.ficha = {"tema": "Pintura", "resumen": "Un capó azul", "usos": ["Detalle del proceso"],
                      "tramos": [{"inicio": 0, "fin": 1.5, "detalle": "Mano sobre el capó"}],
                      "mejor_tramo": "0–1,5 s", "audio": "Sin pista", "limitaciones": "Solo primer plano",
                      "familia": "Capó"}
        self.meta = self.enterContext(patch.object(lib, "inspeccionar", return_value={"duracion": 2}))
        self.agente = self.enterContext(patch.object(lib, "agente", return_value=self.ficha))

    def ciclo(self, t):
        with patch.object(lib.time, "time", return_value=t):
            lib.ciclo(self.root, self.db)

    def test_espera_a_que_termine_la_copia_e_indexa_contenido_nuevo(self):
        path = self.refs / "export.mp4"
        path.write_bytes(b"parcial")
        self.ciclo(100)
        path.write_bytes(b"copia completa")
        self.ciclo(111)
        self.ciclo(123)
        self.agente.assert_not_called()
        self.ciclo(128)
        (self.refs / "duplicado.mov").write_bytes(path.read_bytes())
        (self.refs.parent / "03 - Videos terminados/final.mp4").write_bytes(b"final")
        self.ciclo(130)
        self.ciclo(150)
        self.assertEqual(self.agente.call_count, 1)
        rows = lib.catalogo(self.db, "cuenta.demo")
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["estado"] for r in rows}, {"clasificado"})
        self.assertEqual(len({r["sha256"] for r in rows}), 1)
        self.assertIn("Mano sobre el capó", (self.root / "biblioteca/cuenta.demo/CATALOGO.md").read_text(encoding="utf-8"))
        path.unlink()
        self.ciclo(156)
        self.assertEqual(len(lib.catalogo(self.db,"cuenta.demo")), 1)

    def test_reintenta_y_reconcilia_despues_de_una_interrupcion(self):
        (self.refs.parent / "01 - Videos crudos/bruto.mkv").write_bytes(b"video")
        self.agente.side_effect = [RuntimeError("sin conexión"), self.ficha]
        self.ciclo(500)
        self.ciclo(520)
        self.assertEqual(lib.catalogo(self.db, "cuenta.demo")[0]["estado"], "reintento")
        self.ciclo(525)
        self.assertEqual(self.agente.call_count, 1)
        self.ciclo(570)
        row = lib.catalogo(self.db, "cuenta.demo")[0]
        self.assertEqual(row["estado"], "clasificado")
        self.assertFalse(row["incidencia"])
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO pendientes_catalogo VALUES ('cuenta.demo')")
        (self.root / "biblioteca/cuenta.demo/catalogo.json").unlink()
        self.ciclo(590)
        result = json.loads((self.root / "biblioteca/cuenta.demo/catalogo.json").read_text(encoding="utf-8"))
        self.assertEqual(result[0]["ficha"]["tema"], "Pintura")

    def test_reemplazo_de_video_ilegible(self):
        f = self.refs / "entrada.mp4"
        f.write_bytes(b"moov ausente")
        self.meta.side_effect = [lib.MedioIlegible("moov ausente"), {"duracion":2}]
        self.ciclo(20)
        self.ciclo(40)
        self.assertEqual(lib.catalogo(self.db,"cuenta.demo")[0]["estado"], "ilegible")
        self.agente.assert_not_called()
        f.write_bytes(b"version completa restaurada")
        self.ciclo(50)
        self.ciclo(70)
        self.assertEqual(lib.catalogo(self.db,"cuenta.demo")[0]["estado"], "clasificado")

