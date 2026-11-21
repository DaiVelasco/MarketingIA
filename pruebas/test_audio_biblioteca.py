"""Muestreo de pistas de audio en la biblioteca; funciona también en una PC sin Whisper."""
from array import array
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from herramientas.audio_biblioteca import analizar_audio


class MuestrasAudio(unittest.TestCase):
    def test_sin_pista_y_silencio_solo_en_las_ventanas(self):
        with tempfile.TemporaryDirectory() as tmp, patch("herramientas.audio_biblioteca.subprocess.run") as run:
            informe=analizar_audio(tmp,"clip.mp4",{"audio":[],"duracion":40})
            self.assertEqual(informe["estado"],"sin_pista")
            run.assert_not_called()
            run.return_value=subprocess.CompletedProcess([],0,bytes(7*16000*2),b"")
            informe=analizar_audio(tmp,"clip.mp4",{"audio":["aac"],"duracion":40})
            self.assertEqual(informe["estado"],"silencio_muestreado")
            self.assertEqual([x["inicio"] for x in informe["ventanas"]],[0,16.5,33])
            self.assertIn("solo cubre esos tramos",informe["resumen"])
            self.assertEqual(run.call_count,3)

    def test_fallo_de_whisper_o_configuraciones_invalidas_no_detienen_el_informe(self):
        with tempfile.TemporaryDirectory() as tmp, patch("herramientas.audio_biblioteca.subprocess.run") as run:
            root=Path(tmp)
            (root/".local").mkdir()
            cfg=root/".local/biblioteca-audio.json"
            fuente=root/"sustituto-local"
            fuente.touch()
            cfg.write_text(json.dumps({"habilitar_whisper":True,"python_whisper":str(fuente),
                                       "modelo_whisper":str(fuente),"ventanas":1}),encoding="utf8")
            onda=array("h",[1200]*20+[-1200]*20).tobytes()*80
            pcm=(onda+bytes(len(onda)))*5
            run.side_effect=[subprocess.CompletedProcess([],0,pcm,b""),subprocess.TimeoutExpired("whisper",5)]
            informe=analizar_audio(root,"clip.mp4",{"audio":["aac"],"duracion":7})
            self.assertEqual((informe["estado"],informe["whisper"]),("senal_presente","tiempo_agotado"))
            self.assertTrue(informe["ventanas"])
            self.assertIsNone(informe["transcripcion"])
            cfg.write_text('{"ventanas": 90}',encoding="utf8")
            run.side_effect=[subprocess.CompletedProcess([],0,pcm,b"")]
            informe=analizar_audio(root,"clip.mp4",{"audio":["aac"],"duracion":2})
            self.assertEqual(informe["estado"],"senal_presente")
            self.assertTrue(informe["avisos"])
