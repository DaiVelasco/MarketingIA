import json
from pathlib import Path
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

from herramientas import guion_rodaje as rodaje
from herramientas.edicion_reel import sha256, validar_guion_voz


def guion_de_prueba():
    escena = dict(segundos=6, frases=["f1"], intencion="curioso",
                  toma=dict(quien="La conductora", accion="Señala la marca junto a la válvula.",
                            fin="Deja el dedo junto a la marca."),
                  camara=dict(posicion="A la altura de la rueda.", plano="Detalle", foco="la válvula y el dedo"),
                  edicion=dict(entrada="Entra con la rueda a la vista.", corte="Corta al detenerse el dedo.",
                               enlace="Conserva el gesto al abrir a los dos rostros."),
                  sonido="Ambiente de taller bajo la voz.", texto_grafico=None)
    cierre = dict(escena, segundos=8.4, frases=["f2"], intencion="cercano",
                  toma=dict(quien="El asesor", accion="Sigue el dedo con la mirada.", fin="Asiente."),
                  camara=dict(posicion="Del lado del cliente.", plano="Medio", foco="los dos rostros"),
                  edicion=dict(entrada="Abre sobre la mirada.", corte="Corta tras el asentimiento.",
                               enlace="Mantén ambiente al pasar a blanco."))
    placa = dict(segundos=2.6, frases=[], toma=dict(quien="Firma de Konduce", accion="Aparece el usuario.",
                 fin="Sostén el último cuadro."), camara=dict(posicion="Centro", plano="Placa", foco="la firma"),
                 edicion=dict(entrada="Entra desde el blanco.", corte="Sal tras el cuadro 78.", enlace="Termina en silencio."),
                 sonido="Se extingue el ambiente.", texto_grafico="@konduce.ve")
    return {"titulo": "La marca que queda junto a la válvula",
            "frases": [{"id": "f1", "texto": "¿Cuál de las dos marcas viste?", "objetivo_visual": "Dos marcas visibles."},
                       {"id": "f2", "texto": "Señálala cuando llegues.", "objetivo_visual": "El asesor reconoce la marca."}],
            "rodaje": dict(turno="mañana", tema="Ubicar una marca", motivo="Señalar cuál de dos marcas se vio.",
                           forma="Conversación a pie de rueda", direccion="Seguir el dedo hasta la válvula.",
                           pregunta="¿Cuál de las dos?", respuesta="El asesor identifica la marca junto a la válvula.",
                           pie_de_foto="La válvula te ayuda a ubicar la marca.", cierre="Toma estable y firma centrada.",
                           fuentes_comerciales=[], cta_frase="f2", escenas=[escena, cierre, placa])}


class GuionRodaje(unittest.TestCase):
    def test_hoja_desde_cli_y_turnos_con_revisiones(self):
        with TemporaryDirectory() as tmp:
            cuenta = Path(tmp) / "konduce.ve"
            hoy = cuenta / "2026-11-27"
            base = hoy / "guion"
            base.mkdir(parents=True)
            antiguo = cuenta / "2026-11-26" / "guion"
            antiguo.mkdir(parents=True)
            (antiguo / "voz-reel-01.json").write_text(json.dumps({"titulo": "El reflejo", "frases": [
                {"texto": "Mira el techo.", "objetivo_visual": "El capó refleja las luces."}]}), encoding="utf-8")
            guion = guion_de_prueba()
            for n in (1, 2):
                (base / f"voz-reel-0{n}.json").write_text(json.dumps(guion), encoding="utf-8")
            filas = rodaje.historial(hoy)
            self.assertEqual([f["titulo"] for f in filas], [guion["titulo"], "El reflejo"])
            self.assertIn("voz-reel-02.json", filas[0]["archivo"])
            subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "campana.py"),
                            "validar-guion", str(hoy), "--revision", "2", "--hoja"], capture_output=True, check=True)
            hoja = (base / "rodaje-reel-02.md").read_text(encoding="utf-8")
            for literal in ("6–14.4 s", "14.4–17 s", "(cercano) Señálala cuando llegues.", "Solo sonido de escena.",
                            "la válvula y el dedo", guion["rodaje"]["pie_de_foto"]):
                self.assertIn(literal, hoja)
            guion["rodaje"]["turno"] = "tarde"
            with self.assertRaisesRegex(ValueError, "turno mañana"):
                rodaje.validar_turno(hoy, guion)

    def test_errores_que_deben_volver_a_contenidos(self):
        for campo, valor, mensaje in (("intencion", "plano medio", "intención"), ("frases", ["f2"], "en orden"),
                                       ("segundos", 0, "segundos"), ("camara", {"posicion": "De lado"}, "plano"),
                                       ("edicion", {"entrada": "Al alzar el dedo"}, "corte")):
            with self.subTest(campo=campo):
                guion = guion_de_prueba()
                guion["rodaje"]["escenas"][0][campo] = valor
                with self.assertRaisesRegex(ValueError, mensaje):
                    rodaje.validar(guion)
        guion = guion_de_prueba()
        guion["rodaje"]["cta_frase"] = "f1"
        with self.assertRaisesRegex(ValueError, "última frase"):
            rodaje.validar(guion)
        guion["rodaje"]["cta_frase"] = "f2"
        guion["rodaje"]["fuentes_comerciales"] = [{"dato": "Un precio sin confirmar."}]
        with self.assertRaisesRegex(ValueError, "fuente"):
            rodaje.validar(guion)

    def test_montaje_exige_rodaje_nuevo_sin_reescribir_el_archivo_historico(self):
        with TemporaryDirectory() as tmp:
            hoy = Path(tmp) / "konduce.ve" / "2026-11-27"
            (hoy / "guion").mkdir(parents=True)
            guion = guion_de_prueba()
            del guion["rodaje"]
            (hoy / "guion/voz-reel-01.json").write_text(json.dumps(guion), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Falta rodaje"):
                validar_guion_voz(hoy, 1, 17, {})
            self.assertFalse(rodaje.requiere_rodaje(hoy.with_name("2026-11-26")))
            self.assertFalse(rodaje.requiere_rodaje(Path(tmp) / "otra.cuenta" / hoy.name))

    def test_montaje_vincula_una_toma_sin_voz_a_su_escena(self):
        with TemporaryDirectory() as tmp:
            carpeta = Path(tmp) / "konduce.ve" / "2026-11-27"
            (carpeta / "guion").mkdir(parents=True)
            original = carpeta / "guion/voz-reel-01.json"
            original.write_text(json.dumps(guion_de_prueba()), encoding="utf-8")
            (carpeta / "voz.wav").write_bytes(b"voz de prueba")
            (carpeta / "imagen.mp4").write_bytes(b"toma de prueba")
            srt = carpeta / "voz.srt"
            srt.write_text("1\n00:00:00,100 --> 00:00:03,000\n¿Cuál de las dos marcas viste?\n\n"
                           "2\n00:00:06,100 --> 00:00:08,000\nSeñálala cuando llegues.\n", encoding="utf-8")
            toma = dict(archivo="imagen.mp4", desde=0, hasta=1, motivo="Se ve el gesto de la escena.")
            tomas = [dict(toma, frase="f1", entrada=0, salida=6), dict(toma, frase="f2", entrada=6, salida=14.4),
                     dict(toma, escena=3, entrada=14.4, salida=17)]
            contrato = dict(guion_sha256=sha256(original), voz="voz.wav", voz_sha256=sha256(carpeta / "voz.wav"),
                            subtitulos="voz.srt", tomas=tomas)
            self.assertEqual(validar_guion_voz(carpeta, 1, 17, contrato), sha256(srt))
            tomas[-1]["entrada"] = 7.0
            with self.assertRaisesRegex(ValueError, "se solapa"):
                validar_guion_voz(carpeta, 1, 17, contrato)
