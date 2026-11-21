"""Anima el único detalle de HyperFrames indicado en la hoja de montaje ya validada."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from rutas import CAM, EDIT, PLANTILLA, CODIGO, VERSION, FFMPEG, configuracion, recurso, gsap
HERE=EDIT
from herramientas.edicion_reel import orden_montaje
from herramientas.entrega_archivos import publicar_archivo

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ffmpeg",default=FFMPEG)
    p.add_argument("--escena",type=int,required=True)
    args=p.parse_args()
    orden_montaje(CAM,VERSION)
    plan=json.loads((CAM/"guion"/f"montaje-reel-{CODIGO}.json").read_text(encoding="utf8"))
    seq=plan["guion_voz"]["tomas"][args.escena-1]
    if seq.get("tratamiento")!="hyperframes":
        raise ValueError("La escena elegida debe usar HyperFrames.")
    frames=round(seq["salida"]*30)-round(seq["entrada"]*30)
    duration=frames/30
    src=CAM/seq["archivo"]
    cfg=configuracion()
    paper=recurso(cfg,"papel")
    desde_papel=float(cfg.get("papel_desde",0))
    def ff(*p):
        subprocess.run([args.ffmpeg,"-hide_banner","-loglevel","error","-nostdin","-y",*map(str,p)],check=True)
    with tempfile.TemporaryDirectory(prefix="reel-hyperframes-") as tmp:
        tmp=Path(tmp)
        for folder in ("camara","papel","render"):
            (tmp/folder).mkdir()
        html=(PLANTILLA/"detalle-hyperframes.html").read_text(encoding="utf8").replace("DURACION",str(duration))
        (tmp/"index.html").write_text(html,encoding="utf8")
        shutil.copyfile(gsap(),tmp/"gsap.min.js")
        span=seq["hasta"]-seq["desde"]
        crop=seq.get("reencuadre","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920")
        ff("-ss",seq["desde"],"-threads",2,"-t",span,"-i",src,"-an","-vf",
           f"setpts={duration/span}*(PTS-STARTPTS),fps=30,{crop},setsar=1,tpad=stop_mode=clone:stop_duration=0.25",
           "-frames:v",frames,"-threads",2,"-q:v",2,"-start_number",0,tmp/"camara/%03d.jpg")
        ff("-ss",str(desde_papel),"-threads",2,"-i",paper,"-an","-vf",
           "fps=30,crop=iw*0.58:ih*0.44:iw*0.42:ih*0.39,scale=450:330,format=gray,lut=y='clip((val-64)*3,0,255)'",
           "-frames:v",24,"-threads",2,"-start_number",0,tmp/"papel/%03d.png")
        editable = HERE / "fuentes" / f"hyperframes-{args.escena:02}"
        assets = editable / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        for source in (tmp/"papel").glob("*.png"):
            publicar_archivo(source, assets/("papel-"+source.name))
        publicar_archivo(tmp/"gsap.min.js", assets/"gsap.min.js")
        ff("-framerate",30,"-i",tmp/"camara/%03d.jpg","-an","-c:v","libx264","-crf",12,
           "-pix_fmt","yuv420p","-preset","veryfast","-movflags","+faststart",tmp/"camara.mp4")
        publicar_archivo(tmp/"camara.mp4", assets/"camara.mp4")
        native = (PLANTILLA/"autor-hyperframes.html").read_text(encoding="utf8").replace("DURACION",str(duration))
        (tmp/"editable.html").write_text(native,encoding="utf8")
        publicar_archivo(tmp/"editable.html", editable/"index.html")
        subprocess.run(["node",str(PLANTILLA/"hiper.cjs"),str(tmp),str(tmp/"render"),str(frames)],check=True)
        ff("-framerate",30,"-i",tmp/"render/%03d.jpg","-an","-c:v","libx264","-crf",17,"-pix_fmt","yuv420p",
           "-preset","veryfast","-movflags","+faststart",tmp/"detalle.mp4")
        publicar_archivo(tmp/"detalle.mp4",editable/"inserto.mp4")
if __name__=="__main__":
    main()
