"""Ubicaciones compartidas por los procesos de render. El comando público es motor.py."""
import os
from pathlib import Path
import shutil
import sys

PLANTILLA = Path(__file__).resolve().parent
ROOT = PLANTILLA.parents[1]
sys.path.insert(0, str(ROOT))
from herramientas.edicion_reel import cargar, local

CAM = Path(os.environ["REEL_CAMPANA"]).resolve(strict=True)
VERSION = int(os.environ["REEL_REVISION"])
CODIGO = f"{VERSION:02}"
EDIT = CAM / f"edicion-{CODIGO}"
FFMPEG = os.environ.get("REEL_FFMPEG", "ffmpeg")

def configuracion():
    return cargar(EDIT / "recursos.json")

def recurso(cfg, clave):
    return local(CAM, cfg.get(clave))

def recursos_tinta(cfg, destino):
    """El formato de intercambio son 24 PNG RGBA, s00.png hasta s23.png."""
    carpeta = cfg.get("tinta")
    if not isinstance(carpeta, str) or not carpeta.strip():
        raise ValueError("Indica la carpeta de las transparencias de tinta en recursos.json.")
    destino.mkdir(parents=True, exist_ok=True)
    for i in range(24):
        nombre = f"s{i:02}.png"
        shutil.copyfile(local(CAM, str(Path(carpeta) / nombre)), destino / nombre)

def gsap():
    custom = os.getenv("REEL_GSAP")
    modules = Path(os.getenv("REMOTION_NODE_MODULES", PLANTILLA / "node_modules"))
    path = Path(custom) if custom else modules / "gsap/dist/gsap.min.js"
    return path.resolve(strict=True)

def publicacion():
    return CAM / "Videos del proyecto - Reel de Instagram/03 - Videos terminados" / f"{CODIGO} - Reel.mp4"
