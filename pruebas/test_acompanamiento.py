import array
from math import sin, tau
from pathlib import Path
import shutil
import tempfile
import unittest
import wave

from herramientas.plantilla_reel.ambiente import capas, conformar


FFMPEG = shutil.which("ffmpeg") or Path(__file__).resolve().parents[1] / ".local/ffmpeg.exe"


def pista(path, frecuencia, inicio, fin):
    # Un segundo mono a 24 kHz obliga al mezclador a conformar ambos canales y el reloj.
    datos = array.array("h", (round(3000 * sin(tau * frecuencia * i / 24000)) if inicio <= i / 24000 < fin else 0
                              for i in range(24000)))
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, 24000, 0, "NONE", ""))
        wav.writeframes(datos.tobytes())


@unittest.skipUnless(Path(FFMPEG).is_file(), "La prueba de mezcla necesita FFmpeg.")
class Acompanamiento(unittest.TestCase):
    def test_dos_stems_y_ambiente_heredado(self):
        with tempfile.TemporaryDirectory() as tmp:
            camp = Path(tmp)
            pista(camp / "editorial.wav", 330, 0, .2)
            pista(camp / "clic.wav", 770, .65, .7)
            pista(camp / "ambiente.wav", 220, 0, 1)
            cfg = {"musica": "editorial.wav", "efectos": "clic.wav", "ambiente": "ambiente.wav"}
            seleccion = capas(camp, cfg)
            self.assertEqual(set(seleccion), {"musica", "efectos"})
            wav = camp / "salida.wav"
            conformar(FFMPEG, wav, seleccion, 45)
            with wave.open(str(wav)) as audio:
                self.assertEqual((audio.getnframes(), audio.getframerate(), audio.getnchannels()), (72000, 48000, 2))
                def pico(segundo):
                    audio.setpos(round(segundo * 48000))
                    return max(map(abs, array.array("h", audio.readframes(480))))
                self.assertGreater(pico(.1), 1000)
                self.assertGreater(pico(.67), 1000)
                for segundo in (.4, .85, 1.15):
                    self.assertLessEqual(pico(segundo), 1)

    def test_solo_voz_con_configuracion_anterior(self):
        with tempfile.TemporaryDirectory() as tmp:
            camp = Path(tmp)
            seleccion = capas(camp, {"ambiente": "crudo-historico.wav"})
            self.assertEqual(seleccion, {})
            wav = camp / "acompanamiento.wav"
            conformar(FFMPEG, wav, seleccion, 17)
            with wave.open(str(wav)) as audio:
                self.assertEqual(audio.getnframes(), 17 * 1600)
                self.assertFalse(any(audio.readframes(audio.getnframes())))
