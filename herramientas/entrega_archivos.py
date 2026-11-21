"""Entrega atómica con los permisos de la carpeta de destino, también en Windows."""
import os
from pathlib import Path
import shutil
import uuid


def publicar_archivo(origen, destino):
    origen, destino = Path(origen), Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Los MP4 y WAV que salen de TemporaryDirectory retienen su ACL privada
    # al moverlos dentro del mismo volumen NTFS. Crear el archivo aquí permite
    # que el usuario del escritorio lo abra con los permisos de su proyecto.
    temporal = destino.with_name(f".{destino.name}.{uuid.uuid4().hex}.tmp")
    try:
        with origen.open("rb") as source, temporal.open("xb") as output:
            shutil.copyfileobj(source, output, 1024 * 1024)
        os.replace(temporal, destino)
    finally:
        temporal.unlink(missing_ok=True)
