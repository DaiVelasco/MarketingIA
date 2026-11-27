"""Fija A1 y alinea las palabras del guion aprobado antes de localizar ningún plano."""
import argparse
from difflib import SequenceMatcher
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata
import wave

from rutas import CAM, EDIT, CODIGO, FFMPEG
HERE=EDIT
from herramientas.entrega_archivos import publicar_archivo
from herramientas import guion_rodaje

def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()

def limpio(s):
    s=unicodedata.normalize("NFKD",s.casefold())
    return "".join(c for c in s if c.isalnum())

def tiempo_srt(t):
    ms=round(1000*t)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"

def lineas(texto,max_chars=31):
    tokens=texto.split()
    if len(texto)<=max_chars or len(tokens)<2:
        return texto
    # Escoger el corte más equilibrado sin empezar la segunda línea con puntuación.
    idx=min(range(1,len(tokens)),key=lambda i:abs(len(" ".join(tokens[:i]))-len(" ".join(tokens[i:]))))
    return " ".join(tokens[:idx])+"\n"+" ".join(tokens[idx:])

def alinear(guion,resultado,duracion):
    heard=[w for s in resultado["segments"] for w in s.get("words",[])
           if w.get("end",0)>w.get("start",0) and limpio(w.get("word",""))]
    tokens=[(p["id"],token) for p in guion["frases"] for token in p["texto"].split()]
    normal=[limpio(t) for _,t in tokens]
    recognized=[limpio(w["word"]) for w in heard]
    if len(heard)<2:
        raise ValueError("Whisper no encontró suficientes palabras verificables.")
    anchors={}
    for block in SequenceMatcher(None,normal,recognized,autojunk=False).get_matching_blocks():
        for i in range(block.size):
            w=heard[block.b+i]
            anchors[block.a+i]=(w["start"],w["end"])
    coverage=len(anchors)/len(tokens)
    if coverage<.58:
        raise ValueError(f"Solo coincide el {coverage:.0%} del guion. Revisar la locución antes de editar.")
    times={}
    ix=0
    while ix<len(tokens):
        if ix in anchors:
            times[ix]=anchors[ix]; ix+=1; continue
        left=ix
        while ix<len(tokens) and ix not in anchors:
            ix+=1
        low=anchors[left-1][1] if left else heard[0]["start"]
        high=anchors[ix][0] if ix<len(tokens) else min(duracion,heard[-1]["end"])
        for j in range(left,ix):
            times[j]=(low+(high-low)*(j-left)/(ix-left),low+(high-low)*(j-left+1)/(ix-left))
    words=[{"frase":fid,"texto":t,"inicio":round(times[i][0],3),"fin":round(times[i][1],3),
            "origen":"whisper" if i in anchors else "interpolado_entre_anclas"} for i,(fid,t) in enumerate(tokens)]
    spans=[]
    cues=[]
    for p in guion["frases"]:
        chosen=[w for w in words if w["frase"]==p["id"]]
        spans.append({"id":p["id"],"inicio":chosen[0]["inicio"],"fin":chosen[-1]["fin"]})
        groups=p.get("subtitulos",[p["texto"]])
        if [limpio(s) for g in groups for s in g.split()] != [limpio(w["texto"]) for w in chosen]:
            raise ValueError("Los bloques de subtítulo no coinciden con la frase "+p["id"])
        pos=0
        for g in groups:
            count=len(g.split())
            cues.append({"frase":p["id"],"inicio":chosen[pos]["inicio"],"fin":chosen[pos+count-1]["fin"],
                         "texto":lineas(g)})
            pos+=count
    for i,c in enumerate(cues):
        # Mantener el subtítulo en los cortes internos y suavizar pausas breves entre grupos.
        upper=cues[i+1]["inicio"] if i+1<len(cues) else duracion
        c["fin"]=round(min(upper,c["fin"]+.10),3)
    return {"cobertura":round(coverage,4),"palabras":words,"frases":spans,"subtitulos":cues}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original",type=Path)
    p.add_argument("modelo",type=Path)
    p.add_argument("--ffmpeg",default=FFMPEG)
    args=p.parse_args()
    guionfile=CAM/"guion"/f"voz-reel-{CODIGO}.json"
    guion=json.loads(guionfile.read_text(encoding="utf8"))
    if "rodaje" in guion or guion_rodaje.requiere_rodaje(CAM):
        guion_rodaje.validar(guion)
    import torch
    import whisper
    src=args.original.resolve(strict=True)
    torch.set_num_threads(3)
    def ff(*args_ff):
        subprocess.run([args.ffmpeg,"-hide_banner","-loglevel","error","-nostdin","-y",*map(str,args_ff)],check=True)
    # Las herramientas de render están deliberadamente fuera de esta etapa.
    with tempfile.TemporaryDirectory(prefix="reel-voz-") as tempdir:
        temp=Path(tempdir)
        ff("-i",src,"-vn","-ar",48000,"-ac",2,"-c:a","pcm_s16le",temp/"original.wav")
        with wave.open(str(temp/"original.wav"),"rb") as w:
            samples=w.getnframes()
        pre=.10
        total_frames=math.ceil((samples/48000+pre+2)*30)
        duration=total_frames/30
        ff("-i",temp/"original.wav","-af",f"adelay=100:all=1,apad,atrim=end_sample={total_frames*1600}",
           "-ar",48000,"-ac",2,"-c:a","pcm_s16le",temp/"voz.wav")
        track=temp/"voz.wav"
        # Whisper recibe PCM por memoria. No necesita encontrar otra copia de FFmpeg en PATH.
        import numpy as np
        raw=subprocess.check_output([args.ffmpeg,"-v","error","-i",str(track),"-ac","1","-ar","16000","-f","s16le","-"])
        model=whisper.load_model(str(args.modelo.resolve(strict=True)),device="cpu")
        res=model.transcribe(np.frombuffer(raw,dtype="<i2").astype(np.float32)/32768,language="es",fp16=False,
                             verbose=None,temperature=0,condition_on_previous_text=False,word_timestamps=True)
        sha=digest(track)
        evidence={"modelo":args.modelo.name,"fuente":src.name,"fuente_sha256":digest(src),"voz_sha256":sha,
                  "guion_sha256":digest(guionfile),"transcripcion":res}
        (temp/"whisper-verificacion.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf8")
        alignment=alinear(guion,res,duration)
        alignment.update(voz_sha256=sha,guion_sha256=digest(guionfile),fotogramas=total_frames,duracion=duration)
        (temp/"alineacion.json").write_text(json.dumps(alignment,ensure_ascii=False,indent=2),encoding="utf8")
        text="\n\n".join(f"{i}\n{tiempo_srt(c['inicio'])} --> {tiempo_srt(c['fin'])}\n{c['texto']}" for i,c in enumerate(alignment["subtitulos"],1))
        (temp/"subtitulos.srt").write_text(text+"\n",encoding="utf8")
        publicar_archivo(track,HERE/"pistas/voz.wav")
        publicar_archivo(temp/"whisper-verificacion.json",HERE/"fuentes/whisper-verificacion.json")
        publicar_archivo(temp/"subtitulos.srt",HERE/"subtitulos.srt")
        publicar_archivo(temp/"subtitulos.srt",HERE/"pistas/subtitulos.srt")
        publicar_archivo(temp/"alineacion.json",HERE/"alineacion.json")
        print(json.dumps({"fotogramas":total_frames,"duracion":duration,"guion_sha256":digest(guionfile),
                          "voz_sha256":sha,"cobertura":alignment["cobertura"],"frases":alignment["frases"]},ensure_ascii=False))

if __name__=="__main__":
    main()
