"""Genera una cama sin voz a partir del ambiente real del taller y un pulso propio."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from rutas import CAM, EDIT, FFMPEG, configuracion, recurso
HERE=EDIT
from herramientas.entrega_archivos import publicar_archivo

def crear(ffmpeg, salida):
    align = json.loads((HERE / "alineacion.json").read_text(encoding="utf8"))
    duration = align["fotogramas"] / 30
    samples = align["fotogramas"] * 1600
    cfg = configuracion()
    room = recurso(cfg, "ambiente")
    # Dos parciales suaves, con cadencias distintas, acompañan el trabajo manual.
    pulse = "0.013*sin(2*PI*98*t)*exp(-4.1*mod(t+0.12,0.98))+0.006*sin(2*PI*146.83*t)*exp(-3.8*mod(t+0.37,1.96))"
    pulse = pulse.replace(",", "\\,")
    with tempfile.TemporaryDirectory(prefix="reel-ambiente-") as work:
        wav = Path(work) / "ambiente.wav"
        mix = (f"[0:a]volume={float(cfg.get('ambiente_db',-5.0))}dB,atrim=end_sample={samples}[room];"
               "[1:a]aformat=channel_layouts=stereo[music];"
               f"[room][music]amix=inputs=2:normalize=0,afade=t=in:d=0.18,"
               f"afade=t=out:st={max(0,duration-0.85)}:d={min(0.85,duration)},apad,atrim=end_sample={samples}[a]")
        subprocess.run([str(ffmpeg),"-v","error","-nostdin","-y","-stream_loop","-1","-i",room,
                        "-f","lavfi","-i",f"aevalsrc={pulse}:s=48000:d={duration}","-filter_complex",mix,
                        "-map","[a]","-ar","48000","-ac","2","-c:a","pcm_s16le",wav],check=True)
        publicar_archivo(wav, salida)

if __name__ == "__main__":
    crear(FFMPEG, HERE/"pistas/ambiente.wav")
