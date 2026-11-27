"""Conforma la música y los efectos preparados por Edición al reloj de A1."""
import json
from pathlib import Path
import subprocess
import tempfile

PISTA_A2 = "musica-efectos.wav"


def capas(campana, recursos):
    from herramientas.edicion_reel import local, numero

    seleccion = {}
    for rol in ("musica", "efectos"):
        if recursos.get(rol) is None:
            continue
        ganancia = recursos.get(f"{rol}_db", 0)
        if not numero(ganancia):
            raise ValueError(f"{rol}_db debe ser un número finito en decibelios.")
        seleccion[rol] = (local(campana, recursos[rol]), ganancia)
    return seleccion


def conformar(ffmpeg, salida, seleccion, fotogramas):
    from herramientas.entrega_archivos import publicar_archivo

    muestras = fotogramas * 1600  # 48 kHz / 30 fps.
    entradas = []
    filtros = []
    for indice, (archivo, ganancia) in enumerate(seleccion.values()):
        entradas.extend(["-i", str(archivo)])
        filtros.append(f"[{indice}:a:0]aresample=48000,aformat=channel_layouts=stereo,"
                       f"volume={ganancia}dB[in{indice}]")
    if entradas:
        etiquetas = "".join(f"[in{i}]" for i in range(len(seleccion)))
        filtros.append(f"{etiquetas}amix=inputs={len(seleccion)}:normalize=0,"
                       f"alimiter=limit=0.99:level=0:latency=1,apad,atrim=end_sample={muestras}[a]")
    else:
        filtros.append(f"anullsrc=r=48000:cl=stereo,atrim=end_sample={muestras}[a]")
    with tempfile.TemporaryDirectory(prefix="reel-a2-") as work:
        wav = Path(work) / PISTA_A2
        subprocess.run([str(ffmpeg), "-v", "error", "-nostdin", "-y", *entradas,
                        "-filter_complex", ";".join(filtros), "-map", "[a]", "-ar", "48000",
                        "-ac", "2", "-c:a", "pcm_s16le", wav], check=True)
        publicar_archivo(wav, salida)


def crear(ffmpeg, salida):
    from rutas import CAM, EDIT, configuracion

    reloj = json.loads((EDIT / "alineacion.json").read_text(encoding="utf8"))
    conformar(ffmpeg, salida, capas(CAM, configuracion()), reloj["fotogramas"])

if __name__ == "__main__":
    from rutas import EDIT, FFMPEG
    crear(FFMPEG, EDIT / "pistas" / PISTA_A2)
