"""Renderiza únicamente después de fijar el guion, la pista A1, su SRT y la orden firmada."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from rutas import CAM, EDIT, PLANTILLA, CODIGO, VERSION, FFMPEG, configuracion, publicacion, recursos_tinta
HERE=EDIT
from herramientas.edicion_reel import orden_montaje, sha256
from herramientas.entrega_archivos import publicar_archivo
from herramientas.edicion_reel import leer_subtitulos, local

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    
    ap.add_argument("--ffmpeg",default=FFMPEG)
    ap.add_argument("--salida",type=Path,default=publicacion())
    args=ap.parse_args()
    if args.salida.exists():
        raise ValueError("Elige una ruta libre antes de reconformar.")
    orden_montaje(CAM,VERSION)
    plan=json.loads((CAM/"guion"/f"montaje-reel-{CODIGO}.json").read_text(encoding="utf8"))
    voz=local(CAM,plan["guion_voz"]["voz"])
    subtitulos=local(CAM,plan["guion_voz"]["subtitulos"])
    align=json.loads((HERE/"alineacion.json").read_text(encoding="utf8"))
    if align["voz_sha256"]!=sha256(voz) or align["guion_sha256"]!=sha256(CAM/"guion"/f"voz-reel-{CODIGO}.json"):
        raise ValueError("Cambió A1 o el guion desde la revisión de Whisper.")
    total=align["fotogramas"]
    dur=total/30
    stems=HERE/"pistas"
    def ff(*args_ff):
        subprocess.run([str(args.ffmpeg),"-hide_banner","-nostdin","-v","error","-y",*map(str,args_ff)],check=True)
    def renderizar(publico, destino, propiedades, temporal):
        comando=["node",str(PLANTILLA/"render.cjs"),str(publico),str(destino),str(propiedades),str(temporal)]
        intento=subprocess.run(comando,cwd=PLANTILLA,stderr=subprocess.PIPE,text=True,errors="replace")
        if intento.returncode==0:
            return
        print(intento.stderr,file=sys.stderr)
        if not any(fallo in intento.stderr for fallo in ("write EOF","EPIPE","Target closed")):
            intento.check_returncode()
        # Un encoder o pestaña que se cerró puede recuperarse en serie sin tocar las pistas entregadas.
        print("Reiniciando esta fase de render con un solo proceso.",flush=True)
        subprocess.run(comando,cwd=PLANTILLA,env=dict(os.environ,REEL_CONCURRENCIA="1"),check=True)
    with tempfile.TemporaryDirectory(prefix="reel-remotion-") as s:
        scratch=Path(s)
        public=scratch/"public"; public.mkdir()
        shots=[]
        last=0
        cfg=configuracion()
        for i,shot in enumerate(plan["guion_voz"]["tomas"]):
            f0,f1=round(shot["entrada"]*30),round(shot["salida"]*30)
            if last!=f0 or f1<=f0:
                raise ValueError("Inconsistencia en el reloj de la orden.")
            last=f1
            metadata={"f0":f0,"f1":f1,"fundido":shot.get("fundido",0)}
            origin=CAM/shot["archivo"]
            if shot.get("tratamiento")=="placa":
                key_logo = f"firma-{i}.png"
                shutil.copyfile(origin,public/key_logo)
                metadata["firma"]=key_logo
                metadata["placa"]=True
            else:
                key=f"t{i:02d}"
                dest=public/key; dest.mkdir()
                if shot.get("tratamiento")=="hyperframes":
                    source=HERE/"fuentes"/f"hyperframes-{i+1:02}"/"inserto.mp4"
                    seek=0; span=(f1-f0)/30
                else:
                    source=origin
                    seek=shot["desde"]; span=shot["hasta"]-seek
                factor=(f1-f0)/(30*span)
                base_filter=shot.get("reencuadre","scale=936:1664:force_original_aspect_ratio=increase,crop=936:1664")
                filters=f"setpts={factor}*(PTS-STARTPTS),fps=30,{base_filter},setsar=1,tpad=stop_mode=clone:stop_duration=0.25"
                ff("-ss",seek,"-threads",2,"-t",f"{span:.6f}","-i",source,"-an","-vf",filters,
                   "-frames:v",f1-f0,"-threads",2,"-q:v",2,"-start_number",0,dest/"%03d.jpg")
                if len(list(dest.glob("*.jpg")))!=f1-f0:
                    raise ValueError("Faltan fotogramas de "+origin.name)
                metadata["carpeta"]=key
            shots.append(metadata)
        if last!=total:
            raise ValueError("Los planos no cubren la duración completa.")
        anim=plan.get("acento_tinta")
        if anim:
            recursos_tinta(cfg,public/"tinta")
        # Frases definitivas de salida se leen del mismo SRT validado por el director.
        blocks=subtitulos.read_text(encoding="utf8").strip().split("\n\n")
        srt=leer_subtitulos(subtitulos,dur)
        cues=[{"inicio":ini,"fin":fin,"texto":"\n".join(block.splitlines()[2:])} for (ini,fin,_),block in zip(srt,blocks,strict=True)]
        props=scratch/"props.json"
        opciones={"fotogramas":total,"planos":shots,"subtitulos":[],"tinta":anim}
        props.write_text(json.dumps(opciones,ensure_ascii=False),encoding="utf8")
        from ambiente import crear
        crear(args.ffmpeg,scratch/"ambiente.wav")
        renderizar(public,scratch/"imagen.mp4",props,scratch)
        opciones["subtitulos"]=cues
        props.write_text(json.dumps(opciones,ensure_ascii=False),encoding="utf8")
        renderizar(public,scratch/"con-subtitulos.mp4",props,scratch)
        ff("-i",scratch/"con-subtitulos.mp4","-i",voz,"-i",scratch/"ambiente.wav","-filter_complex",
           f"[1:a]volume={float(cfg.get('voz_db',0))}dB[voz];[voz][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.96:level=0:latency=1[a]","-map","0:v:0","-map","[a]",
           "-c:v","copy","-c:a","aac","-b:a","192k","-ar",48000,"-movflags","+faststart","-t",dur,scratch/"final.mp4")
        ff("-xerror","-i",scratch/"final.mp4","-map","0:v:0","-map","0:a:0","-f","null","-")
        publicar_archivo(scratch/"imagen.mp4",stems/"imagen.mp4")
        publicar_archivo(scratch/"ambiente.wav",stems/"ambiente.wav")
        if voz.resolve()!=(stems/"voz.wav").resolve():
            publicar_archivo(voz,stems/"voz.wav")
        publicar_archivo(scratch/"final.mp4",args.salida)
    print(args.salida)

if __name__=="__main__":
    main()
