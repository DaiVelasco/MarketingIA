from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import json

from campana import ROOT, VIDEO, account_name, start
from herramientas.orden_carrusel import orden_carrusel
from herramientas.edicion_reel import HERRAMIENTAS, orden_montaje, sha256


class Expediente(unittest.TestCase):
    def test_orden_reel_vincula_voz_subtitulos_y_toma_a_la_frase(self):
        with TemporaryDirectory() as tmp:
            folder = start(Path(tmp), "cuenta.demo", "2026-11-21")
            script = folder / "guion/voz-reel-01.json"
            script.write_text(json.dumps({"frases": [
                {"id": "f1", "texto": "Mira el borde.", "objetivo_visual": "Se ve la curva."},
                {"id": "f2", "texto": "Sigue la línea.", "objetivo_visual": "Se ve el trazo."}
            ]}), encoding="utf-8")
            voice = folder / "voz.wav"
            voice.write_bytes(b"voz grabada")
            srt = folder / "frases.srt"
            subtitles = "1\n00:00:00,100 --> 00:00:01,000\nMira el borde.\n\n2\n00:00:01,100 --> 00:00:02,000\nSigue la línea.\n"
            srt.write_text(subtitles, encoding="utf-8")
            (folder / "curva.mp4").write_bytes(b"metraje")
            orders = [{"id": tool, "herramienta": tool, "entrada": 0, "salida": 2,
                       "instruccion": "Componer", "insumo": "Material", "resultado": "Plano"} for tool in HERRAMIENTAS]
            plan_file = folder / "guion/montaje-reel-01.json"
            plan = {"duracion": 2, "ordenes": orders}
            plan_file.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Falta guion_voz"):
                orden_montaje(folder, 1)
            shots = [{"frase": f"f{i+1}", "archivo": "curva.mp4", "desde": i, "hasta": i+1,
                      "entrada": i, "salida": i+1, "motivo": "Se distingue la curva."} for i in range(2)]
            plan["guion_voz"] = {"guion_sha256": sha256(script), "voz": "voz.wav", "voz_sha256": sha256(voice),
                                 "subtitulos": "frases.srt", "tomas": shots}
            plan_file.write_text(json.dumps(plan), encoding="utf-8")
            self.assertEqual(orden_montaje(folder, 1)["subtitulos_sha256"], sha256(srt))
            for plugin, skill in (("efectos-converzzo", "parallax-3d"), ("tipografia-converzzo", "gancho")):
                self.assertNotIn(plugin, orden_montaje(folder, 1)["asignacion"])
                orders.append({**orders[0], "id": plugin, "herramienta": plugin, "skill": skill})
                plan_file.write_text(json.dumps(plan), encoding="utf-8")
                self.assertEqual(orden_montaje(folder, 1)["asignacion"][plugin], [plugin])
            orders[-1]["skill"] = "parallax-3d"
            plan_file.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no pertenece a tipografia-converzzo"):
                orden_montaje(folder, 1)
            orders[-1].pop("skill")  # Orden histórica con la operación en texto libre.
            plan_file.write_text(json.dumps(plan), encoding="utf-8")
            srt.write_text(subtitles.replace("Sigue", "Corta"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "texto de todo"):
                orden_montaje(folder, 1)
            srt.write_text(subtitles, encoding="utf-8")
            shots[1].update(entrada=0, salida=1)
            plan_file.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "voz de f2"):
                orden_montaje(folder, 1)
            voice.write_bytes(b"otra voz")
            with self.assertRaisesRegex(ValueError, "locución cambió"):
                orden_montaje(folder, 1)

    def test_orden_carrusel_vincula_cada_lamina_a_su_foto(self):
        with TemporaryDirectory() as tmp:
            folder = start(Path(tmp), "cuenta.demo", "2026-11-21")
            image = folder / "carrusel" / "foto.jpg"
            image.write_bytes(b"foto de prueba")
            plan = {"objetivo": "Observar el reflejo", "cuenta": "cuenta.demo",
                    "formato": [1080, 1350], "cta": "Guárdalo."}
            slide = {"titulo": "Mira el reflejo", "cuerpo": "", "imagen": "carrusel/foto.jpg",
                     "recorte": "Capó centrado", "capas": ["Foto", "Texto"],
                     "tipografia": "Archivo", "posicion": "Arriba", "control": "Se ve la luz",
                     "alt": "Luz reflejada en un capó"}
            plan["laminas"] = [dict(slide, numero=i) for i in range(1, 5)]
            path = folder / "guion" / "carrusel-01.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            self.assertIn("carrusel/foto.jpg", orden_carrusel(folder, 1)["imagenes"])
            plan["laminas"][2]["capas"] = []
            path.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "lámina 3"):
                orden_carrusel(folder, 1)
            plan["laminas"][2]["capas"] = slide["capas"]
            path.write_text(json.dumps(plan), encoding="utf-8")
            image.unlink()
            with self.assertRaisesRegex(ValueError, "ausente"):
                orden_carrusel(folder, 1)

    def test_carpeta_de_video_y_reanudacion(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            name = account_name("https://www.instagram.com/cuenta.demo/")
            folder = start(root, name, "2026-11-21")
            expected = ["01 - Videos crudos", "02 - Referencias", "03 - Videos terminados"]
            self.assertEqual(sorted(x.name for x in (folder / VIDEO).iterdir()), expected)
            self.assertTrue(all((folder / VIDEO / item).is_dir() for item in expected))
            brief = folder / "brief.md"
            brief.write_text("Acuerdo del equipo", encoding="utf-8")
            self.assertEqual(start(root, name, "2026-11-21"), folder)
            self.assertEqual(brief.read_text(encoding="utf-8"), "Acuerdo del equipo")

    def test_perfiles_del_equipo(self):
        import tomllib
        profiles = set()
        for path in (ROOT / ".codex/agents").glob("*.toml"):
            profile = tomllib.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(profile["name"], path.stem)
            self.assertTrue(profile["developer_instructions"].strip())
            profiles.add(profile["name"])
        self.assertEqual(profiles, {"investigacion", "analitica", "reservas", "ventas", "crecimiento",
                                    "conversion", "contenidos", "editor_video", "diseno", "revision",
                                    "publicacion", "comunidad", "bibliotecario_video"})
