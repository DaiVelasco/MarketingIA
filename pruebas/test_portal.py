import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from herramientas.aprendizaje import historial
from portal import codificar, importar, preparar, sha256


class IntercambioDePropuestas(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.campana = self.root / "campanas" / "prueba" / "2026-11-21"
        self.portal = self.campana / "portal"
        self.portal.mkdir(parents=True)
        self.retorno = self.root / "decision.json"
        opciones = []
        for clave, formato in [("reel-01", "reel"), ("carrusel-02", "carrusel")]:
            nombres = ["01.mp4"] if formato == "reel" else [f"{n:02}.jpg" for n in range(1, 5)]
            opciones.append({
                "id": clave, "formato": formato, "version": int(clave[-2:]), "titulo": clave,
                "rasgos": ["luz natural"], "archivos": [self.archivo(f"entrega/{clave}/{n}") for n in nombres],
                "revision_editorial": self.archivo(f"revision/{clave}.md"),
                "caption": self.archivo(f"entrega/{clave}/caption.txt"),
            })
        self.catalogo = {"cuenta": "prueba", "jornada": "2026-11-21", "id": "2026-11-21/feed", "opciones": opciones}
        (self.portal / "catalogo.json").write_bytes(codificar(self.catalogo))

    def archivo(self, nombre):
        path = self.campana / nombre
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"contenido de ensayo {nombre}", encoding="utf-8")
        return {"archivo": nombre, "sha256": sha256(path)}

    def decision(self, paquete, **cambios):
        dato = {"id": self.catalogo["id"], "cuenta": "prueba", "paquete_sha256": sha256(paquete),
                "fecha": "2026-11-21T14:00:00-04:00", "revision": 1, "elegida": "reel-01"}
        self.retorno.write_bytes(codificar(dato | cambios))
        return importar(self.campana, self.retorno)

    def test_paquete_reproducible_idempotencia_correccion_y_atribucion(self):
        paquete = preparar(self.campana)
        huella = sha256(paquete)
        self.assertEqual(huella, sha256(preparar(self.campana)))
        with ZipFile(paquete) as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(8, len(z.namelist()))
            self.assertFalse(any("revision/" in nombre for nombre in z.namelist()))
        path = self.decision(paquete, opciones=[{"rasgos": ["atribución falsa"]}])
        self.assertEqual(path, self.decision(paquete))
        cambios = {"elegida": "carrusel-02", "revision": 2, "fecha": "2026-11-21T15:00:00-04:00",
                   "motivo_admin": "Prefiero las fotos."}
        self.decision(paquete, **cambios)
        recibo = json.loads(path.read_bytes())
        op = self.catalogo["opciones"][1]
        self.assertEqual(recibo["huella_publicacion"], ":".join(["carrusel", *(i["sha256"] for i in op["archivos"]), op["caption"]["sha256"]]))
        self.assertEqual((recibo["cuenta"], recibo["revision_memoria"], recibo["archivos"], recibo["version_pieza"]),
                         ("prueba", 2, op["archivos"], 2))
        hechos = historial(self.root, "prueba", "decision", self.catalogo["id"])
        self.assertEqual(len(hechos), 2)
        self.assertEqual(hechos[-1]["evento"]["opciones"][0]["rasgos"], ["luz natural"])
        with self.assertRaisesRegex(ValueError, "desactualizada"):
            self.decision(paquete)

    def test_rechaza_paquete_version_o_archivo_diferentes(self):
        paquete = preparar(self.campana)
        for change in ({"paquete_sha256":"0"*64}, {"cuenta":"otra"}, {"id":"otra"}, {"elegida":"tercera"},
                       {"fecha":"2026-11-21T09:00:00"}, {"revision":2}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.decision(paquete, **change)
        with ZipFile(paquete, "a") as z:
            z.writestr("intruso.txt", "sin registrar")
        with self.assertRaisesRegex(ValueError, "adicionales"):
            self.decision(paquete)
        preparar(self.campana)
        (self.campana / "entrega/reel-01/01.mp4").write_bytes(b"cambio")
        with self.assertRaisesRegex(ValueError, "huella"):
            self.decision(paquete)
        self.assertFalse((self.portal / "seleccion.json").exists())

    def test_cli_dos_rondas_con_archivos_e_historiales_independientes(self):
        paquete1 = preparar(self.campana)
        seleccion1 = self.decision(paquete1)
        originales = {p: sha256(p) for p in (paquete1, seleccion1, self.portal / "catalogo.json")}
        ronda = self.portal / "ronda-02"
        ronda.mkdir()
        segundo = {**self.catalogo, "id": "2026-11-21/grafica-todoterreno"}
        (ronda / "catalogo.json").write_bytes(codificar(segundo))
        cli = [sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "portal.py")]
        subprocess.run([*cli, "preparar", self.campana, "--ronda", "ronda-02"], check=True, capture_output=True)
        paquete2 = ronda / "propuestas.zip"
        self.assertNotEqual(sha256(paquete1), sha256(paquete2))
        self.assertFalse((ronda / "seleccion.json").exists())
        with self.assertRaisesRegex(ValueError, "otra cuenta, conjunto o versión"):
            importar(self.campana, self.retorno, ronda="ronda-02")
        eleccion2 = {**json.loads(self.retorno.read_bytes()), "id": segundo["id"],
                     "paquete_sha256": sha256(paquete2), "elegida": "carrusel-02"}
        self.retorno.write_bytes(codificar(eleccion2))
        subprocess.run([*cli, "importar", "--ronda", "ronda-02", self.campana, self.retorno], check=True, capture_output=True)
        with self.assertRaisesRegex(ValueError, "otra cuenta, conjunto o versión"):
            importar(self.campana, self.retorno)
        self.assertEqual((ronda / "seleccion.json").resolve(), importar(self.campana, self.retorno, ronda="ronda-02"))
        self.assertEqual("carrusel-02", json.loads((ronda / "seleccion.json").read_bytes())["elegida"])
        for grupo in (segundo["id"], self.catalogo["id"]):
            self.assertEqual(1, len(historial(self.root, "prueba", "decision", grupo)))
        self.assertEqual(originales, {path: sha256(path) for path in originales})

    def test_slug_e_identificador_de_ronda(self):
        for slug in ("", "..", "../portal", "a/b", "CON", "con", "aux", "ronda.2"):
            with self.subTest(slug=slug), self.assertRaisesRegex(ValueError, "slug"):
                preparar(self.campana, ronda=slug)
        ronda = self.portal / "ronda-02"
        ronda.mkdir()
        (ronda / "catalogo.json").write_bytes(codificar(self.catalogo))
        with self.assertRaisesRegex(ValueError, "id distinto"):
            preparar(self.campana, ronda="ronda-02")
        self.assertFalse((ronda / "propuestas.zip").exists())
