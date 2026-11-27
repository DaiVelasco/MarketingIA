import importlib.util
import io
import json
import os
from email.message import Message
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import HTTPError


SCRIPT = Path(__file__).resolve().parents[1] / "skills/diseno-sonido/scripts/openverse.py"
SPEC = importlib.util.spec_from_file_location("openverse_audio", SCRIPT)
ov = importlib.util.module_from_spec(SPEC)
if importlib.util.find_spec("numpy"):
    SPEC.loader.exec_module(ov)


def respuesta(datos):
    body = io.BytesIO(json.dumps(datos).encode())
    body.headers = Message()
    body.headers["Content-Type"] = "application/json"
    return body


@unittest.skipUnless(importlib.util.find_spec("numpy"), "Ejecutar con el entorno de edición de audio.")
class OpenverseAudio(unittest.TestCase):
    def setUp(self):
        ov._token, ov._expira = "", 0.0

    def test_oauth_reutiliza_token_y_mantiene_credenciales_fuera_del_proveedor(self):
        hit = dict(id="123456789", url="https://proveedor.example/efecto.ogg", license="cc0",
                   title="Obturador", duration=500, source="ejemplo")
        media = io.BytesIO(b"audio de prueba")
        responses = [respuesta({"access_token": "ejemplo", "expires_in": 3600}),
                     respuesta({"results": [hit]}), media, respuesta({"results": []})]
        env = {"OPENVERSE_CLIENT_ID": "prueba", "OPENVERSE_CLIENT_SECRET": "secreto-de-prueba"}
        with (TemporaryDirectory() as tmp, patch.dict(os.environ, env, clear=True),
              patch.object(ov.urllib.request, "urlopen", side_effect=responses) as red,
              patch.object(ov, "medir", return_value={"dur": 0.5}),
              patch.multiple(ov, BASE=Path(tmp), DEST=Path(tmp)/"openverse", MANI=Path(tmp)/"manifiesto.json")):
            self.assertEqual(len(ov.bajar("clic", ["obturador"])), 1)
            self.assertEqual(ov.buscar("sin resultados"), [])
            requests = [call.args[0] for call in red.call_args_list]
            self.assertEqual(requests[0].full_url, ov.TOKEN_URL)
            self.assertIn(b"grant_type=client_credentials", requests[0].data)
            self.assertIn(b"client_secret=secreto-de-prueba", requests[0].data)
            self.assertEqual(requests[1].get_header("Authorization"), "Bearer ejemplo")
            self.assertNotIn("Authorization", requests[1].headers)  # no se reenvía en redirecciones
            self.assertIsNone(requests[2].get_header("Authorization"))
            self.assertEqual(requests[3].get_header("Authorization"), "Bearer ejemplo")
            self.assertEqual(ov.lista("clic")[0]["licencia"], "cc0")

    def test_challenge_se_distingue_de_cero_resultados_y_no_se_reintenta(self):
        error = HTTPError(ov.API, 403, "Forbidden", {"cf-mitigated": "challenge", "cf-ray": "ray-prueba"}, None)
        with patch.dict(os.environ, {}, clear=True), patch.object(ov.urllib.request, "urlopen", side_effect=error) as red:
            with self.assertRaisesRegex(ov.ErrorOpenverse, "403.*audio.*ray-prueba"):
                ov.buscar("obturador")
            red.assert_called_once()

    def test_un_par_incompleto_no_envia_peticion(self):
        with patch.dict(os.environ, {"OPENVERSE_CLIENT_ID": "id"}, clear=True), patch.object(ov.urllib.request, "urlopen") as red:
            with self.assertRaisesRegex(ov.ErrorOpenverse, "Configura juntas"):
                ov.buscar("obturador")
            red.assert_not_called()
